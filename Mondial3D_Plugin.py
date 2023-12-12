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
import threading

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

    
    else:
        context.scene.error = "Cannot connect to the server. Please try again!"
     
def receiveSearchLabels(context):
    url="https://api.mondial3d.studio/api/Nft/all-labels"
    response= requests.get(url)
    if response.status_code ==200:
        response=response.json()
        global search_labels
        search_labels= response
        return True
    else:
        context.scene.error = "Cannot connect to the server. Please try again!"
        return False

def autocomplete_search(context):
    global search_labels
    user_input = context.scene.my_search_prop
    exact_match = [word for word in search_labels if word.lower() == user_input.lower()]
    suggestions = [word for word in search_labels if word.lower().startswith(user_input.lower())]
    
    if len(exact_match) > 0:
        suggestions.remove(exact_match[0])
        suggestions.insert(0, exact_match[0])
    
    return suggestions

def update_function(context):
    suggestions = autocomplete_search(context)
    if len(suggestions) > 0:
        context.scene.my_search_prop = suggestions[0]
    else:
        context.scene.my_search_prop = ""


class OBJECT_PT_MondialPanel(Panel):
    bl_label= "Mondial"
    bl_idname= "OBJECT_PT_MondialPanel"
    bl_category= "Mondial"
    bl_region_type= "UI"
    bl_space_type= "VIEW_3D"

    def draw(self, context):
        if not context.scene.error == "":
            layout = self.layout
            row = layout.row()
            row.label(text=context.scene.error)

        if context.scene.user == "":
            layout = self.layout
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
                if not context.scene.ai_scene_prompt_obj == "":
                    row= box.row()
                    if not context.scene.ai_scene_prompt_loader:
                        row.operator("mondial.ai_scene_prompt_download_operator")
                    else:
                        row.label(text="LOADING...")

            # Marketplace
            layout = self.layout
            row = layout.row()
            row.label(text="Marketplace")
            row = layout.row()

            if not context.scene.marketplace_activation:
                row.operator("mondial.marketplace_operator")
            else:
                global image_previews

                if not context.scene.marketplace_loader:
                    # Search Bar
                    row.prop(context.scene, "my_search_prop")
                    row = layout.row()
                    row.operator("mondial.filter_model_marketplace")

                    # Marketplace Items
                    if image_previews:
                        box = layout.box()
                        for image_name, icon_id in image_previews.items():
                            row = box.row()
                            row.template_icon(icon_value=icon_id, scale=4.0)
                            row = box.row()
                            if not context.scene.marketplace_download_loader:
                                op=row.operator("mondial.load_model_marketplace")
                                op.image_name= image_name
                            else: 
                                row.label(text="LOADING...")
                            
                        # Navigation Button
                        row = layout.row()
                        if context.scene.pageID == 1:
                            row.operator("mondial.next_model_marketplace")
                        elif context.scene.pageID > 1 :
                            row.operator("mondial.prev_model_marketplace")
                            row.operator("mondial.next_model_marketplace")
                    elif not (len(image_previews)>0):
                        row = layout.row()
                        row.operator("mondial.marketplace_operator")
                    

                else:
                    row = layout.row()
                    row.label(text="LOADING...")

            # Publish to server
            layout = self.layout
            row = layout.row()
            row.label(text="Publish To Server")
            row = layout.row()
            row.operator("mondial.publish_to_server")
                

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
            context.scene.error= "You are not Authorized - 401"
        else:
            context.scene.error = "Cannot connect to the server. Please try again!"

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

    def modal(self, context, event):
        if not self.thread.is_alive():
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.thread = threading.Thread(target=self.apply_prompt, args=(context,))
        self.thread.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def apply_prompt(self, context):
        if not context.scene.ai_scene_prompt=="":
            api_url = f"https://api.mondial3d.studio/api/Nft/ai-Add-complete-scene?categoryName={context.scene.ai_scene_prompt}"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                data = data["completeScene"]
                context.scene.ai_scene_prompt_info = data["labels"]
                context.scene.ai_scene_prompt_obj = data["fileLink"]
                print("Downloading...")
            else:
                print("Can not connect to the server, Please try again!")
        else:
            return True

class AIPromptSceneDownloadOperator(Operator):
    bl_idname = "mondial.ai_scene_prompt_download_operator"
    bl_label = "Download the Scene"

    # Add a new property to hold the path of the downloaded file
    file_path: bpy.props.StringProperty(default="")

    def modal(self, context, event):
        if not self.thread.is_alive():
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            # If a file was downloaded, import it
            if self.file_path:
                bpy.ops.import_scene.gltf(filepath=self.file_path)
                context.scene.ai_scene_prompt_info=""
                context.scene.ai_scene_prompt_obj=""
                context.scene.ai_scene_prompt_loader = False
                self.file_path = ""  # Clear the file path

            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.thread = threading.Thread(target=self.download_and_load_scene, args=(context,))
        self.thread.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def download_and_load_scene(self, context):
        context.scene.ai_scene_prompt_loader = True
        global temp_dir
        save_path =""

        print("Downloading...")

        response= requests.get(context.scene.ai_scene_prompt_obj)

        if response.status_code == 200:
            save_path = os.path.join(temp_dir, "model.glb")
            with open(save_path, 'wb') as f:
                f.write(response.content)

            # Instead of importing the model here, store the path in the file_path property
            self.file_path = save_path
                
        else:
            print("Can not connect to the server, Please try again!")


class MarketPlace(Operator):
    bl_idname = "mondial.marketplace_operator"
    bl_label = "Activate Marketplace"

    def modal(self, context, event):
        if not self.thread.is_alive():
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        context.scene.marketplace_activation=True
        self.thread = threading.Thread(target=self.download_and_receive, args=(context,))
        self.thread.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def download_and_receive(self, context):
        print("Downloading...")
        context.scene.marketplace_loader = True

        downloadMarketplaceModel(context)
        receiveSearchLabels(context)

        context.scene.marketplace_loader=False

class MarketPlaceModelDownload(Operator):
    bl_idname = "mondial.load_model_marketplace"
    bl_label = "Download and Load Model"
    image_name: bpy.props.StringProperty()

    # Add a new property to hold the path of the downloaded file
    file_path: bpy.props.StringProperty(default="")

    def modal(self, context, event):
        if not self.thread.is_alive():
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            # If a file was downloaded, import it
            if self.file_path:
                bpy.ops.import_scene.gltf(filepath=self.file_path)
                context.scene.marketplace_download_loader= False
                self.file_path = ""  # Clear the file path

            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.thread = threading.Thread(target=self.download_and_load_model, args=(context,))
        self.thread.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def download_and_load_model(self, context):
        print("Downloading...")
        context.scene.marketplace_download_loader= True
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

                # Instead of importing the model here, store the path in the file_path property
                self.file_path = save_path
        else:
            print("Can not connect to the server, Please try again!")
             
class NextModelMarketPlace(Operator):
    bl_idname = "mondial.next_model_marketplace"
    bl_label = "Next"

    def modal(self, context, event):
        if not self.thread.is_alive():
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        context.scene.pageID +=1
        self.thread = threading.Thread(target=downloadMarketplaceModel, args=(context,))
        self.thread.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
class PrevModelMarketPlace(Operator):
    bl_idname = "mondial.prev_model_marketplace"
    bl_label = "Prev"

    def modal(self, context, event):
        if not self.thread.is_alive():
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        if context.scene.pageID != 1:
            context.scene.pageID -=1
        self.thread = threading.Thread(target=downloadMarketplaceModel, args=(context,))
        self.thread.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
class ApplyFilterMarketPlace(Operator):
    bl_idname = "mondial.filter_model_marketplace"
    bl_label = "Apply"
    
    def modal(self, context, event):
        if not self.thread.is_alive():
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.thread = threading.Thread(target=self.apply_filter, args=(context,))
        self.thread.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def apply_filter(self, context):
        context.scene.marketplace_loader = True

        update_function(context)
        downloadMarketplaceModel(context)

        context.scene.marketplace_loader = False

class ExportMyScene(Operator):
    bl_idname = "mondial.publish_to_server"
    bl_label = "Export My Scene To Server"

    global temp_dir
    _timer = None
    output_path = os.path.join(temp_dir, "file.glb")
    post_status_code = None  # Add this line

    def modal(self, context, event):
        if event.type == 'TIMER':
            # Condition to stop the operator.
            if self.condition_to_stop_is_met():
                self.cancel(context)
                return {'FINISHED'}

            # Condition to export the scene.
            if self.condition_to_export_is_met():
                self.export_scene(context)

        return {'PASS_THROUGH'}

    def execute(self, context):
        if self.condition_to_export_is_met():
            self.export_scene(context)
        else:
            self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
            context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)

    def condition_to_stop_is_met(self):
        # Stop when the POST request status code is 200.
        return self.post_status_code == 200  # Update this line

    def condition_to_export_is_met(self):
        # Export when all mesh objects are selected.
        objs = bpy.context.scene.objects
        for obj in objs:
            if obj.type == 'MESH' and not obj.select_get():
                return False
        return True

    def export_scene(self, context):
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Select all mesh objects
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)

        # Export selected objects to .glb
        bpy.ops.export_scene.gltf(filepath=self.output_path + ".glb")
        print("Exporting..")

        # Create New Project on Mondial3d.com
        create_url = "https://api.mondial3d.studio/api/Nft/create-project"
        print(context.scene.login_token)
        headers = {"Authorization": "Bearer " + context.scene.login_token}
        response = requests.get(create_url, headers=headers)
        if response.status_code == 200:
            projectID = response.json()
            headers = {"Authorization": "Bearer " + context.scene.login_token,
                       "projectid": projectID}
            update_url = "https://api.mondial3d.studio/api/Nft/update-project"
            with open(self.output_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(update_url, headers=headers, files=files)
                self.post_status_code = response.status_code

            print(response.status_code)
        else:
            print("Can not connect to the server, Please try again!")

def register():
    #Variables
    bpy.types.Scene.error = bpy.props.StringProperty()
    
    # 
    bpy.types.Scene.login_token = bpy.props.StringProperty(name="Auth Token", default="")
    bpy.types.Scene.user = bpy.props.StringProperty(default= "")
    # 
    bpy.types.Scene.ai_scene_prompt = bpy.props.StringProperty(name="AI Scene Prompt")
    bpy.types.Scene.ai_scene_prompt_info= bpy.props.StringProperty(default= "")
    bpy.types.Scene.ai_scene_prompt_obj= bpy.props.StringProperty(default= "")
    bpy.types.Scene.ai_scene_prompt_loader= bpy.props.BoolProperty(default= False)
    # 
    bpy.types.Scene.marketplace_activation= bpy.props.BoolProperty(default= False)
    bpy.types.Scene.pageID = bpy.props.IntProperty(default= 1)
    bpy.types.Scene.marketplace_loader= bpy.props.BoolProperty(default= False)
    bpy.types.Scene.marketplace_download_loader= bpy.props.BoolProperty(default= False)
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

    # Publish To Server
    bpy.utils.register_class(ExportMyScene)
    
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

    # Publish To Server
    bpy.utils.unregister_class(ExportMyScene)
    

    #Variables
    del bpy.types.Scene.error
    # 
    del bpy.types.Scene.login_token
    del bpy.types.Scene.user
    # 
    del bpy.types.Scene.ai_scene_prompt
    del bpy.types.Scene.ai_scene_prompt_info
    del bpy.types.Scene.ai_scene_prompt_obj
    del bpy.types.Scene.ai_scene_prompt_loader
    # 
    del bpy.types.Scene.marketplace_activation
    del bpy.types.Scene.marketplace_loader
    del bpy.types.Scene.marketplace_download_loader
    del bpy.types.Scene.pageID
    del bpy.types.Scene.my_search_prop


if __name__ == "__main__":
    register()
