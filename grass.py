from pico2d import load_image # 내가 필요한것만 임포트할 수 있다. 

class Grass:
    def __init__(self):
        self.image = load_image('grass.png')

    def draw(self):
        self.image.draw(400, 30)

    def update(self):
        pass