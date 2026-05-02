class Animation:
    """Simple frame-based animation with configurable frame duration."""
    def __init__(self, frames, frame_duration=0.12):
        self.frames = frames
        self.frame_duration = frame_duration
        self.timer = 0.0
        self.current = 0

    def update(self, dt):
        if len(self.frames) <= 1:
            return
        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.current = (self.current + 1) % len(self.frames)

    def get_image(self):
        return self.frames[self.current]

    def reset(self):
        self.timer = 0.0
        self.current = 0
