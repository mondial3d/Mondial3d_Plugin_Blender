bl_info = {
    "name": "Mondial3D Plugin",
    "author": "Amirsaleh Naderzadeh Mehrabani",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Panel> Mondial",
    "description": "Mondial Blender Plugin.",
    "category": "3D View",
}



from tarfile import data_filter
import bpy
from bpy.types import Panel, Operator
import requests
import os
import tempfile

temp_dir = tempfile.gettempdir()
auth= False
user= None
pageid = 1
custom_icons = None
IMAGE_PATH = ""
MODEL_URL = ""
nftId = ""
image_needs_reload = False

class mondialPanel(Panel):
    bl_label= "Mondial"
    bl_idname= "Mondial"
    bl_category= "Mondial"
    bl_region_type= "UI"
    bl_space_type= "VIEW_3D"

    def draw(self, context):
        global custom_icons
        layout = self.layout
        global auth
        if auth == False:
            layout = self.layout
            row = layout.row()
            row.prop(context.scene, "login_token")
            row = layout.row()
            row.operator("mondial.login_operator")
            row = layout.row()
            row.operator("mondial.signup_operator")
        else:
            layout= self.layout

            global user
            box= layout.box()
            row= box.row()
            row.alignment = 'CENTER'
            row.label(text=user, icon="BLENDER")
            
            box=layout.box()
            box.prop(context.scene, "ai_scene_prompt")
            box=box.row()
            box.operator("mondial.ai_scene_prompt_operator")

            global IMAGE_PATH
            global custom_icons
            global pageid
            global nftId
            
            layout = self.layout
            box = layout.box()
            row = box.row()
            if pageid == 1:
                row.operator("mondial.next_model_marketplace")
            elif pageid > 1 :
                row.operator("mondial.prev_model_marketplace")
                row.operator("mondial.next_model_marketplace")

            download_image()
            load_image()
            
            # Preview Image inside the panel
            if not custom_icons:
                custom_icons = bpy.utils.previews.new()
                custom_icons["image_icon"] = custom_icons.load("image_icon", IMAGE_PATH, 'IMAGE')
            row= box.row()
            row.template_icon(custom_icons["image_icon"].icon_id, scale=6)
            
            # Downlaod Model Button
            row = box.row()
            row.operator("mondial.load_model_marketplace", icon= "NLA_PUSHDOWN")


     
class SignupOperator(Operator):
    bl_idname = "mondial.signup_operator"
    bl_label = "Signup"

    def execute(self, context):
        login_url = "https://www.mondial3d.com/login-center"
        bpy.ops.wm.url_open(url=login_url)

        return {'FINISHED'}

class LoginOperator(Operator):
    bl_idname = "mondial.login_operator"
    bl_label = "Login"

    def execute(self, context):
        global auth
        global user
        token= context.scene.login_token
        base_url = "https://api.mondial3d.studio/api/Nft/GetProfile"
        headers={"Authorization" : "Bearer "+ token}
        response = requests.get(base_url, headers=headers)
        if response.status_code == 200 : 
            auth= True
            data= response.json()
            user= data["email"]

        else: 
            auth= False
        return {'FINISHED'}

class AIPromptSceneOperator(Operator):
    bl_idname = "mondial.ai_scene_prompt_operator"
    bl_label = "Apply Prompt"

    def execute(self, context):
        global temp_dir
        api_text = context.scene.ai_scene_prompt
        api_url = f"https://api.mondial3d.studio/api/Nft/ai-Add-complete-scene?categoryName={api_text}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            data = data["completeScene"]
            model_url = data["fileLink"]
            
            file = requests.get(model_url)
            
            if file.status_code == 200: 
                save_path = os.path.join(temp_dir, "{}.glb".format(data["name"]))  
                with open(save_path, 'wb') as f:
                    f.write(file.content)
                          
                bpy.ops.import_scene.gltf(filepath = save_path)

        return {'FINISHED'}

def download_image():
    
    global image_needs_reload
    
    global pageid
    global temp_dir 
    global MODEL_URL
    global IMAGE_PATH
    global nftId
    
    MODEL_URL = ""
    IMAGE_PATH = ""
    
    take = 1
    url = f"https://api.mondial3d.studio/api/Nft/blendernfts?pageid={pageid}&take={take}"
    image_base_url = "https://cdn.mondial3d.com/"
        
    # Getting data from url
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        data = data["listNFTs"]
        obj= data[0]
        
        #Getting Image From Server
        image_url = image_base_url + obj["imageAdress"]
        save_path = os.path.join(temp_dir, obj["imageAdress"])
            
        response = requests.get(image_url)
        if response.status_code == 200:
                
            IMAGE_PATH = save_path
            MODEL_URL = obj["url"]
            nftId= obj["nftId"]
                
            with open(save_path, 'wb') as f:
                f.write(response.content)
    
    image_needs_reload = True

def load_image():
    global IMAGE_PATH, image_needs_reload

    # Check if the image needs to be reloaded
    if not image_needs_reload:
        return

    # Load the image if it's not already loaded
    if IMAGE_PATH not in bpy.data.images:
        bpy.data.images.load(IMAGE_PATH, check_existing=True)

    image_needs_reload = False

class LoadModelMarketPlace(Operator):
    bl_idname = "mondial.load_model_marketplace"
    bl_label = "Download and Load Model"
    
    def execute(self, context):
        global MODEL_URL
        global temp_dir 
        request_url= f"https://api.mondial3d.studio/api/Nft/Download3D?URL={MODEL_URL}"
        
        response = requests.get(request_url)
        if response.status_code == 200:
            url = response.content
                
            file = requests.get(url)
            
            if file.status_code == 200: 
                save_path = os.path.join(temp_dir, f"{MODEL_URL}.glb")  
                with open(save_path, 'wb') as f:
                    f.write(file.content)
                          
                bpy.ops.import_scene.gltf(filepath = save_path)    
                return {'FINISHED'} 
                     
class NextModelMarketPlace(Operator):
    bl_idname = "mondial.next_model_marketplace"
    bl_label = "Next"

    def execute(self, context):
        global pageid
        global custom_icons
        if custom_icons:
            bpy.utils.previews.remove(custom_icons)
        pageid +=1
        return {'FINISHED'}

class PrevModelMarketPlace(Operator):
    bl_idname = "mondial.prev_model_marketplace"
    bl_label = "Prev"

    def execute(self, context):
        global pageid
        global custom_icons
        if custom_icons:
            bpy.utils.previews.remove(custom_icons)
        if pageid != 1:
            pageid -=1
            return {'FINISHED'}


def register():
    #Login
    bpy.utils.register_class(mondialPanel)
    bpy.utils.register_class(LoginOperator)
    bpy.utils.register_class(SignupOperator)
    bpy.types.Scene.login_token = bpy.props.StringProperty(name="Auth Token")

    #AI
    bpy.utils.register_class(AIPromptSceneOperator)
    bpy.types.Scene.ai_prompt = bpy.props.StringProperty(name="AI Prompt")
    bpy.types.Scene.ai_scene_prompt = bpy.props.StringProperty(name="AI Scene Prompt")

    #Marketplace
    bpy.utils.register_class(LoadModelMarketPlace)
    bpy.utils.register_class(NextModelMarketPlace)
    bpy.utils.register_class(PrevModelMarketPlace)

def unregister():
    #Login
    bpy.utils.unregister_class(mondialPanel)
    bpy.utils.unregister_class(LoginOperator)
    bpy.utils.unregister_class(SignupOperator)
    del bpy.types.Scene.login_token

    #AI
    bpy.utils.register_class(AIPromptSceneOperator)
    del bpy.types.Scene.ai_prompt
    del bpy.types.Scene.ai_scene_prompt
    
    global custom_icons
    if custom_icons:
        bpy.utils.previews.remove(custom_icons)
    bpy.utils.unregister_class(LoadModelMarketPlace)
    bpy.utils.unregister_class(NextModelMarketPlace)
    bpy.utils.unregister_class(PrevModelMarketPlace)


if __name__ == "__main__":
    register()
