from utils.image_utils import load_image_from_file
from controllers.clipboard_controller import get_image_from_clipboard


class ImageController:
    def __init__(self):
        self.current_image = None

    def load_from_file(self, path):
        self.current_image = load_image_from_file(path)
        return self.current_image

    def load_from_clipboard(self):
        image = get_image_from_clipboard()
        if image is not None:
            self.current_image = image
        return image

    def get_current_image(self):
        return self.current_image
