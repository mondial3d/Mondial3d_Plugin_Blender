bl_info = {
    "name": "Mondial3D Plugin",
    "author": "Amirsaleh Naderzadeh Mehrabani",
    "version": (1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Panel> Mondial",
    "description": "Mondial Blender Plugin.",
    "category": "3D View",
}

import bpy
from bpy.types import Panel, Operator
import bpy.utils.previews
import requests
import os
import tempfile

temp_dir = tempfile.gettempdir()
image_previews = {}
search_labels=[]

def checkAuthentication(token):
    base_url = "https://api.mondial3d.studio/api/Nft/GetProfile"
    headers={"Authorization" : "Bearer "+ token}
    response = requests.get(base_url, headers=headers)

    return response

def downloadMarketplaceModel(context):
    global temp_dir
    global image_previews

    take = 3
    if context.scene.my_search_prop == "":
        url = f"https://api.mondial3d.studio/api/Nft/blendernfts?pageid={context.scene.pageID}&take={take}"
    else:
        url = f"https://api.mondial3d.studio/api/Nft/blendernfts?pageid={context.scene.pageID}&take={take}&Labels={context.scene.my_search_prop}"
    image_base_url = "https://cdn.mondial3d.com/"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        marketplace_data = data["listNFTs"]

        preview_collection = bpy.utils.previews.new()
        image_previews.clear()
        print("Downloading")

        for i in marketplace_data:
            image_url = image_base_url + i["imageAdress"]
            save_path = os.path.join(temp_dir, i["imageAdress"])

            response = requests.get(image_url)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)

                # Load image for preview
                image_name = i["url"]
                preview = preview_collection.load(image_name, save_path, 'IMAGE')
                image_previews[image_name] = preview.icon_id
            else:
                context.scene.error = "Cannot connect to the server. Please try again!"
        return True
        

    else:
        context.scene.error = "Cannot connect to the server. Please try again!"   
        return False

def receiveSearchLabels():
    url="https://api.mondial3d.studio/api/Nft/all-labels"
    response= requests.get(url)
    if response.status_code ==200:
        response=response.json()
        global search_labels
        search_labels= response
        return True

def autocomplete_search(context):
    global search_labels
    user_input = context.scene.my_search_prop
    suggestions = [word for word in search_labels if word.lower().startswith(user_input.lower())]
    return suggestions

def update_function(context):
    suggestions = autocomplete_search(context)
    context.scene.my_search_prop=suggestions[0]


class OBJECT_PT_MondialPanel(Panel):
    bl_label= "Mondial"
    bl_idname= "OBJECT_PT_MondialPanel"
    bl_category= "Mondial"
    bl_region_type= "UI"
    bl_space_type= "VIEW_3D"

    def draw(self, context):

        if context.scene.user == "":
            layout = self.layout
            row = layout.row()

            if context.scene.error =="401":
                row= layout.label(text="You are not authorized")

            row = layout.row()
            row.prop(context.scene, "login_token")
            row = layout.row()
            row.operator("mondial.login_operator")
            row = layout.row()
            row.operator("mondial.signup_operator")
        else:
            # User Info And Signout
            layout= self.layout
            box= layout.box()
            row= box.row()
            row.label(text= f"Email : {context.scene.user}")
            row.operator("mondial.signout_operator", icon= "UNLINKED")

            # AI Prompt Scene
            row= layout.row()
            row.label(text="AI")
            box= layout.box()
            row= box.row()
            row.alignment = 'EXPAND'
            row.prop(context.scene, "ai_scene_prompt")
            row=box.row()
            row.operator("mondial.ai_scene_prompt_operator")
            
            # AI Prompt Scene Download
            if context.scene.error== "":
                if not context.scene.ai_scene_prompt_info=="":
                    row= box.row()
                    info= context.scene.ai_scene_prompt_info
                    info= info.split(",")
                    row= box.row()
                    row.label(text= "Scene Labels:")
                    for i in range(len(info)):
                        if i %2 ==0:
                            row= box.row()
                        row.label(text= info[i])
                    if not context.scene.ai_scene_prompt_obj =="":
                        row= box.row()
                        row.operator("mondial.ai_scene_prompt_download_operator")
            else:
                row= box.row()
                row.label(text= context.scene.error)

            # Marketplace
            layout = self.layout
            row = layout.row()
            row.label(text="Marketplace")
            row = layout.row()

            if not context.scene.marketplace_activation:
                row.operator("mondial.marketplace_operator")
            else:
                if context.scene.loading== False:
                    if context.scene.error == "":
                        # Search Bar
                        row.prop(context.scene, "my_search_prop")
                        row = layout.row()
                        row.operator("mondial.filter_model_marketplace")

                        # Marketplace Items
                        box = layout.box()
                        global image_previews
                        if image_previews:
                            for image_name, icon_id in image_previews.items():
                                row = box.row()
                                row.template_icon(icon_value=icon_id, scale=4.0)
                                row = box.row()
                                # please adjust the operator code that Pass image_name to the operator class
                                op=row.operator("mondial.load_model_marketplace")
                                op.image_name= image_name
                            
                            # Navigation Button
                            row = layout.row()
                            if context.scene.pageID == 1:
                                row.operator("mondial.next_model_marketplace")
                            elif context.scene.pageID > 1 :
                                row.operator("mondial.prev_model_marketplace")
                                row.operator("mondial.next_model_marketplace")

                    else:
                        row = box.row()
                        row.label(text=context.scene.error)
                else:
                    row= box.row()
                    row.label(text="Loading")

class SignupOperator(Operator):
    bl_idname = "mondial.signup_operator"
    bl_label = "Signup"

    def execute(self, context):
        login_url = "https://www.mondial3d.com/wallet"
        bpy.ops.wm.url_open(url=login_url)

        return {'FINISHED'}

class LoginOperator(Operator):
    bl_idname = "mondial.login_operator"
    bl_label = "Login"

    def execute(self, context):
        response = checkAuthentication(context.scene.login_token)

        if response.status_code == 200 : 
            data= response.json()
            context.scene.user=data["email"]
            context.scene.error= ""

        elif response.status_code == 401:
            context.scene.error= "401"

        return {'FINISHED'}

class SignoutOperation(Operator):
    bl_idname = "mondial.signout_operator"
    bl_label = "Signout"

    def execute(self, context):
        context.scene.user=""
        context.scene.login_token=""
        context.scene.ai_scene_prompt=""
        context.scene.ai_scene_prompt_info=""
        context.scene.ai_scene_prompt_obj=""
        context.scene.marketplace_activation= False
        context.scene.pageID=1
        context.scene.my_search_prop=""

        return {'FINISHED'}

class AIPromptSceneOperator(Operator):
    bl_idname = "mondial.ai_scene_prompt_operator"
    bl_label = "Apply Prompt"

    def execute(self, context):
        # global temp_dir
        api_url = f"https://api.mondial3d.studio/api/Nft/ai-Add-complete-scene?categoryName={context.scene.ai_scene_prompt}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            data = data["completeScene"]
            context.scene.ai_scene_prompt_info = data["labels"]
            context.scene.ai_scene_prompt_obj = data["fileLink"]
        else:
            context.scene.error="Can not connect to the server, Please try again!"

        return {'FINISHED'}

class AIPromptSceneDownloadOperator(Operator):
    bl_idname = "mondial.ai_scene_prompt_download_operator"
    bl_label = "Download the Scene"

    def execute(self, context):
        global temp_dir

        response= requests.get(context.scene.ai_scene_prompt_obj)

        save_path =""
        if response.status_code == 200:
            save_path = os.path.join(temp_dir, "model.glb")
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
        else:
            context.scene.error="Can not connect to the server, Please try again!"

        if context.scene.error=="":
            bpy.ops.import_scene.gltf(filepath = save_path)
            context.scene.ai_scene_prompt_info=""
            context.scene.ai_scene_prompt_obj=""

        return {'FINISHED'}

class MarketPlace(Operator):
    bl_idname = "mondial.marketplace_operator"
    bl_label = "Activate Marketplace"

    def execute(self, context):
        context.scene.marketplace_activation=True
        s1=downloadMarketplaceModel(context)
        s2=receiveSearchLabels()
        if s1 and s2:
            context.scene.loading=False
        return {'FINISHED'}

class MarketPlaceModelDownload(Operator):
    bl_idname = "mondial.load_model_marketplace"
    bl_label = "Download and Load Model"

    image_name: bpy.props.StringProperty()

    def execute(self, context):
        global temp_dir
        request_url= f"https://api.mondial3d.studio/api/Nft/Download3D?URL={self.image_name}"
        response = requests.get(request_url)
        if response.status_code == 200:
            url = response.content
            file = requests.get(url)
            if file.status_code == 200: 
                save_path = os.path.join(temp_dir, f"{self.image_name}.glb") 

                with open(save_path, 'wb') as f:
                    f.write(file.content)
                          
                bpy.ops.import_scene.gltf(filepath = save_path)    
                return {'FINISHED'} 
        
        return {'FINISHED'} 

class NextModelMarketPlace(Operator):
    bl_idname = "mondial.next_model_marketplace"
    bl_label = "Next"

    def execute(self, context):
        context.scene.pageID +=1
        downloadMarketplaceModel(context)
        return {'FINISHED'}
    
class PrevModelMarketPlace(Operator):
    bl_idname = "mondial.prev_model_marketplace"
    bl_label = "Prev"

    def execute(self, context):
        if context.scene.pageID != 1:
            context.scene.pageID -=1
        downloadMarketplaceModel(context)
        
        return {'FINISHED'}

class ApplyFilterMarketPlace(Operator):
    bl_idname = "mondial.filter_model_marketplace"
    bl_label = "Apply"

    def execute(self, context):

        update_function(context)
        downloadMarketplaceModel(context)

        return {'FINISHED'}

def register():
    #Variables
    bpy.types.Scene.error = bpy.props.StringProperty()
    bpy.types.Scene.loading= bpy.props.BoolProperty(default= True)
    # 
    bpy.types.Scene.login_token = bpy.props.StringProperty(name="Auth Token", default="")
    bpy.types.Scene.user = bpy.props.StringProperty(default= "")
    # 
    bpy.types.Scene.ai_scene_prompt = bpy.props.StringProperty(name="AI Scene Prompt")
    bpy.types.Scene.ai_scene_prompt_info= bpy.props.StringProperty(default= "")
    bpy.types.Scene.ai_scene_prompt_obj= bpy.props.StringProperty(default= "")
    # 
    bpy.types.Scene.marketplace_activation= bpy.props.BoolProperty(default= False)
    bpy.types.Scene.pageID = bpy.props.IntProperty(default= 1)

    bpy.types.Scene.my_search_prop = bpy.props.StringProperty(name = "Filter", default= "")

    #Authentication
    bpy.utils.register_class(OBJECT_PT_MondialPanel)
    bpy.utils.register_class(LoginOperator)
    bpy.utils.register_class(SignupOperator)
    bpy.utils.register_class(SignoutOperation)

    # AI Prompt
    bpy.utils.register_class(AIPromptSceneOperator)
    bpy.utils.register_class(AIPromptSceneDownloadOperator)

    # Marketplace
    bpy.utils.register_class(MarketPlace)
    bpy.utils.register_class(MarketPlaceModelDownload)
    bpy.utils.register_class(NextModelMarketPlace)
    bpy.utils.register_class(PrevModelMarketPlace)
    bpy.utils.register_class(ApplyFilterMarketPlace)
    


def unregister():

    global image_previews
    bpy.utils.previews.remove(image_previews)

    #Authentication
    bpy.utils.unregister_class(OBJECT_PT_MondialPanel)
    bpy.utils.unregister_class(LoginOperator)
    bpy.utils.unregister_class(SignupOperator)
    bpy.utils.unregister_class(SignoutOperation)

    # AI Prompt
    bpy.utils.unregister_class(AIPromptSceneOperator)
    bpy.utils.unregister_class(AIPromptSceneDownloadOperator)

    # Marketplace
    bpy.utils.unregister_class(MarketPlace)
    bpy.utils.unregister_class(MarketPlaceModelDownload)
    bpy.utils.unregister_class(NextModelMarketPlace)
    bpy.utils.unregister_class(PrevModelMarketPlace)
    bpy.utils.unregister_class(ApplyFilterMarketPlace)

    #Variables
    del bpy.types.Scene.login_token
    del bpy.types.Scene.error
    del bpy.types.Scene.loading
    del bpy.types.Scene.user
    del bpy.types.Scene.ai_scene_prompt
    del bpy.types.Scene.ai_scene_prompt_info
    del bpy.types.Scene.ai_scene_prompt_obj
    del bpy.types.Scene.marketplace_activation
    del bpy.types.Scene.pageID
    del bpy.types.Scene.my_search_prop

    


if __name__ == "__main__":
    register()
