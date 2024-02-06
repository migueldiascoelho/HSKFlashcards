import os
from kivy.core.audio import SoundLoader

class AudioManager:
    audio_folder = "All HSK Words"
    active_sound = None
    is_sound_enabled = True  # Global variable to control sound state

    @staticmethod
    def play_audio(chinese_word):
        if not AudioManager.is_sound_enabled:
            return

        audio_file = os.path.join(AudioManager.audio_folder, f"{chinese_word}.mp3")
        sound = SoundLoader.load(audio_file)
        if sound:
            if AudioManager.active_sound:
                AudioManager.active_sound.stop()  # Stop the currently playing sound
            sound.play()
            AudioManager.active_sound = sound  # Set the active sound

    @staticmethod
    def toggle_sound():
        AudioManager.is_sound_enabled = not AudioManager.is_sound_enabled


