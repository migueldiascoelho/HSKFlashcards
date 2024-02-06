from kivymd.app import MDApp
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from score_manager import ScoreManager
from learned_status_manager import LearnedStatusManager
from proficiency_calculator import calculate_hsk_completion
from proficiency_calculator import calculate_user_level
from audio_manager import AudioManager
import os
import csv
import random


class Flashcard(BoxLayout):
    def __init__(self, chinese, pinyin, english, card_count, fold_size, hsk, **kwargs):
        super(Flashcard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.chinese = chinese
        self.pinyin = pinyin
        self.english = english
        self.count = card_count
        self.fold = fold_size
        self.is_flipped = False
        self.first_flip = True
        self.audio_played = False # Flag to track if audio has been played
        self.hsk = hsk[0]



        graphics_folder = os.path.join(os.path.dirname(__file__), 'Graphics')

        # Get the absolute path to the image file
        image_path = os.path.join(graphics_folder, f'flashcard_background{self.hsk}.jpg')
        frame_image_path = os.path.join(graphics_folder, 'flashcard_frame4.png')

        # Add an image as the background to the flashcard
        with self.canvas.before:
            Color(1, 1, 1, 1)  # Set the color to white
            self.background = Rectangle(pos=(0, 0), size=(Window.width, Window.height), source=image_path)

        frame_width, frame_height = 400, 400  # Set the size of the frame
        frame_x = (Window.width - frame_width) / 2
        frame_y = (Window.height - frame_height) / 2

        with self.canvas.before:
            self.frame = Rectangle(pos=(frame_x, frame_y), size=(frame_width, frame_height), source=frame_image_path)

        self.chinese_label = Label(
            text=chinese,
            font_size=90,
            font_name='Han',
            halign='center',
            valign='middle',
            text_size=(300, None),
            size_hint_y=None,
            height=-240,
            color=(0, 0, 0, 1)
        )
        self.pinyin_label = Label(
            text=pinyin,
            font_size=50,
            font_name='Han',
            halign='center',
            valign='middle',
            text_size=(300, None),
            size_hint_y=None,
            height=-400,
            color=(0, 0, 0, 1)
        )
        self.english_label = Label(
            text=f"({english})",
            font_size=30,
            font_name='Han',
            halign='center',
            valign='top',
            text_size=(300, None),
            size_hint_y=None,
            height=650,
            color=(0, 0, 0, 1)  # Adjust this value as needed
        )
        self.counter_label_chinese = Label(
            text=f'{self.count}/{self.fold}'.replace('[', '').replace(']', ''),
            font_size=16,
            font_name='Noto',
            halign='center',
            valign='middle',
            text_size=(300, None),
            size_hint_y=None,
            height=520,

            color=(0, 0, 0, 1)  # Adjust this value as needed
        )

        self.counter_label_pinyin = Label(
            text=f'{self.count}/{self.fold}'.replace('[', '').replace(']', ''),
            font_size=16,
            font_name='Noto',
            halign='center',
            valign='middle',
            text_size=(300, None),
            size_hint_y=None,
            height=520,

            color=(0, 0, 0, 1)  # Adjust this value as needed
        )


        self.add_widget(self.chinese_label)
        self.add_widget(self.counter_label_chinese)

    def on_touch_down(self, touch):
        if not self.is_flipped:
            self.flip_card_pinyin()
        return super(Flashcard, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.is_flipped:
            swipe_distance = touch.x - touch.opos[0]
            if swipe_distance > 60:  # Swiped right
                self.add_to_bad()
            elif swipe_distance < -60:  # Swiped left
                self.add_to_good()
            self.flip_card_chinese()
            return True
        return super(Flashcard, self).on_touch_up(touch)

    def flip_card_chinese(self):
        self.remove_widget(self.pinyin_label)
        self.remove_widget(self.english_label)
        self.add_widget(self.chinese_label)
        self.add_widget(self.counter_label_chinese)
        self.is_flipped = False

    def flip_card_pinyin(self):
        self.remove_widget(self.chinese_label)
        self.remove_widget(self.counter_label_chinese)
        self.add_widget(self.pinyin_label)
        self.add_widget(self.english_label)
        self.is_flipped = True

        if not self.audio_played:  # Only play audio if not played before
            AudioManager.play_audio(self.chinese)
            self.audio_played = True  # Mark audio as played

    def add_to_good(self):
        app = MDApp.get_running_app()
        app.good_flashcards.append(self.chinese)

        chinese_word = app.flashcards[app.current_card_index]["chinese"]
        hsk_level = app.flashcards[app.current_card_index]["hsk_level"]
        app.learned_status_manager.update_status(chinese_word, 1, hsk_level)
        app.flashcards.pop(app.current_card_index)
        app.swipe_count += 1
        app.card_count += 1
        app.next_flashcard("left")

    def add_to_bad(self):
        app = MDApp.get_running_app()
        app.swipe_count += 1
        chinese_word = app.flashcards[app.current_card_index]["chinese"]
        hsk_level = app.flashcards[app.current_card_index]["hsk_level"]
        app.learned_status_manager.update_status(chinese_word, -1, hsk_level)
        app.bad_flashcards.append(self.chinese)
        app.next_flashcard("right")


class FlashcardApp(MDApp):
    def build(self):
        self.score_manager = ScoreManager()
        self.learned_status_manager = LearnedStatusManager()
        LabelBase.register(name='Han', fn_regular='Source Han Sans CN Light.otf')
        LabelBase.register(name='Noto', fn_regular='NotoSansSC-Light.ttf')

        screen_width = 360
        screen_height = 640

        Window.size = (screen_width, screen_height)
        Window.minimum_width = screen_width
        Window.minimum_height = screen_height

        self.flashcards = []
        self.current_card_index = 0
        self.swipe_count = 0
        self.card_count = 1
        self.good_flashcards = []
        self.bad_flashcards = []
        self.difficult = False
        self.sound = True
        self.count = 0
        self.user_name = 'Miguel'
        self.fold_size = None
        self.hsk = None

        menu_layout = RelativeLayout()

        # Get the absolute path to the "Graphics" folder
        graphics_folder = os.path.join(os.path.dirname(__file__), 'Graphics')

        # Get the absolute path to the image file
        image_path = os.path.join(graphics_folder, 'gradient_background_v4.png')

        hsk1_button_image_path = os.path.join(graphics_folder, 'HSK1.png')
        hsk1_back_image_path = os.path.join(graphics_folder, 'HSK1_back.png')
        hsk2_button_image_path = os.path.join(graphics_folder, 'HSK2.png')
        hsk2_back_image_path = os.path.join(graphics_folder, 'HSK2_back.png')
        hsk3_button_image_path = os.path.join(graphics_folder, 'HSK3.png')
        hsk3_back_image_path = os.path.join(graphics_folder, 'HSK3_back.png')
        hsk4_button_image_path = os.path.join(graphics_folder, 'HSK4.png')
        hsk4_back_image_path = os.path.join(graphics_folder, 'HSK4_back.png')
        hsk5_button_image_path = os.path.join(graphics_folder, 'HSK5.png')
        hsk5_back_image_path = os.path.join(graphics_folder, 'HSK5_back.png')
        hsk6_button_image_path = os.path.join(graphics_folder, 'HSK6.png')
        hsk6_back_image_path = os.path.join(graphics_folder, 'HSK6_back.png')
        lvl_button_image_path = os.path.join(graphics_folder, 'LEVEL DISPLAY.png')
        sound_on_button_image_path = os.path.join(graphics_folder, 'volumeOn.png')

        button_size = (170, 190)
        f_size = 50


        greeting_label = Label(
            text=f'你好',
            font_size=26,
            font_name = "Noto",
            color = (0,0,0,1),
            bold=True,
            pos=(-141, 324),
            halign='left'
        )

        greeting_label2 = Label(
            text=f'{self.user_name}',
            font_size=30,
            font_name = "Roboto",
            color = (0,0,0,1),
            bold=True,
            pos=(-118, 286),
            halign='left'
        )


        learn_button_1 = Button(
            size_hint=(None, None),
            font_size = f_size,
            size=button_size,
            background_normal = hsk1_button_image_path,
            background_down = hsk1_back_image_path,
            pos_hint={'center_x': (90/360)+0.02, 'center_y': ((640 / 1.3) / 640)-0.058},
        )

        learn_button_2 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal= hsk2_button_image_path,
            background_down = hsk2_back_image_path,
            pos_hint={'center_x': (270/360)-0.02, 'center_y': ((640 / 1.3) / 640)-0.058},
        )

        learn_button_3 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal = hsk3_button_image_path,
            background_down = hsk3_back_image_path,
            pos_hint={'center_x': (90/360)+0.02, 'center_y': ((640/2)/640)-0.062},
        )
        learn_button_4 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal = hsk4_button_image_path,
            background_down = hsk4_back_image_path,
            pos_hint={'center_x': (270/360)-0.02, 'center_y': ((640/2)/640)-0.062},
        )

        learn_button_5 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal = hsk5_button_image_path,
            background_down = hsk5_back_image_path,
            pos_hint={'center_x': (90/360)+0.02, 'center_y': ((640 / 4.4) / 640)-0.062},
        )
        learn_button_6 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal = hsk6_button_image_path,
            background_down = hsk6_back_image_path,
            pos_hint={'center_x': (270/360)-0.02, 'center_y': ((640 / 4.4) / 640)-0.062},
        )

        see_progress = Button(
            size_hint=(None, None),
            size=(120,82),
            font_size = 28,
            color =(0,0,0,1),
            background_normal='',  # Set background_normal to an empty string
            background_down='',  # Set background_down to an empty string
            background_color=(0, 0, 0, 0),
            pos_hint={'center_x': 0.76, 'center_y': 0.884},
        )

        see_progress2 = Button(
            size_hint=(None, None),
            size=(120,82),
            font_size = 15,
            color =(0,0,0,1),
            background_normal='',  # Set background_normal to an empty string
            background_down='',  # Set background_down to an empty string
            background_color=(0, 0, 0, 0),
            pos_hint={'center_x': 0.76, 'center_y': 0.932},
        )

        sound_button = Button(
            size_hint=(None, None),
            size=(76,76),
            background_normal=sound_on_button_image_path,
            background_down=sound_on_button_image_path,
            pos_hint={'center_x': 0.86, 'center_y': 0.995},
        )

        quit_button = Button(
            text="Quit",
            size_hint=(None, None),
            size=(200, 40),
            background_normal='',
            background_color=(0.400, 0.957, 0.429, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.05},
        )

        see_progress.font_name = "Noto"
        see_progress.text = f'[b][font=Roboto]LVL: {calculate_user_level()} [/font]级[/b]'
        see_progress.markup = True

        see_progress2.text = f'{self.learned_status_manager.get_learned_words_count()} words discovered\n{self.learned_status_manager.get_mastered_words_count()} words mastered'





        learn_button_1.bind(on_release=lambda instance: self.select_fold(1))
        learn_button_2.bind(on_release=lambda instance: self.select_fold(2))
        learn_button_3.bind(on_release=lambda instance: self.select_fold(3))
        learn_button_4.bind(on_release=lambda instance: self.select_fold(4))
        learn_button_5.bind(on_release=lambda instance: self.select_fold(5))
        learn_button_6.bind(on_release=lambda instance: self.select_fold(6))
        see_progress.bind(on_release=lambda instance: self.my_progress())
        see_progress2.bind(on_release=lambda instance: self.my_progress())
        sound_button.bind(on_release=self.toggle_sound)
        quit_button.bind(on_release=self.quit_app)

        self.sound_button = sound_button

        # Set the color for menu buttons

        quit_button.background_color = (0.400, 0.957, 0.429, 0)



        menu_layout.add_widget(learn_button_1)
        menu_layout.add_widget(learn_button_2)
        menu_layout.add_widget(learn_button_3)
        menu_layout.add_widget(learn_button_4)
        menu_layout.add_widget(learn_button_5)
        menu_layout.add_widget(learn_button_6)
        menu_layout.add_widget(greeting_label)
        menu_layout.add_widget(greeting_label2)
        #menu_layout.add_widget(learn_button_x)
        menu_layout.add_widget(see_progress)
        menu_layout.add_widget(see_progress2)
        menu_layout.add_widget(sound_button)
        #menu_layout.add_widget(quit_button)


        # Create the Popup with the background image
        self.menu_popup = Popup(title="", content=menu_layout, size_hint=(1, 1), size=(900, 820),
                                auto_dismiss=True, background=image_path, separator_color=[1, 1, 1, 0])

        # Show the menu when the app starts
        self.menu_popup.open()

        # Create a BoxLayout for your app's content
        self.layout = RelativeLayout()

        return self.layout


    def select_fold(self, level):

        self.value = level

        exit_anim = Animation(opacity=0, duration=0.4)
        exit_anim2 = Animation(opacity=0, duration=0.4)

        # Start the exit animation for the buttons
        for child in self.menu_popup.content.children:
            exit_anim.start(child)
        exit_anim2.start(self.menu_popup)
        self.menu_popup.dismiss()

        # Get the absolute path to the "Graphics" folder
        graphics_folder = os.path.join(os.path.dirname(__file__), 'Graphics')
        normal_button_image_path = os.path.join(graphics_folder, 'normal_fold2.png')
        normal_button_expl_image_path = os.path.join(graphics_folder, 'normal_fold3.png')
        rare_button_image_path = os.path.join(graphics_folder, 'rare_fold2.png')
        rare_button_expl_image_path = os.path.join(graphics_folder, 'rare_fold3.png')
        level_background_image_path = os.path.join(graphics_folder, 'gradient_background_v4.png')

        background_image = Image(source=level_background_image_path, size_hint=(1, 1), pos=(0, 0))
        self.layout.add_widget(background_image)



        normal_fold_button = Button(
            size_hint=(None, None),
            size=(410, 230),
            background_normal=normal_button_image_path,
            background_down=normal_button_expl_image_path,
            pos_hint={'center_x': 0.5, 'center_y': 0.7},
        )
        rare_fold_button = Button(
            size_hint=(None, None),
            size=(410, 230),
            background_normal=rare_button_image_path,
            background_down=rare_button_expl_image_path,
            pos_hint={'center_x': 0.5, 'center_y': 0.3},
        )


        normal_fold_button.bind(on_release=lambda instance: self.update_hsk(self.value))
        rare_fold_button.bind(on_release=lambda instance: self.difficult_words(self.value))


        self.layout.add_widget(normal_fold_button)
        self.layout.add_widget(rare_fold_button)

    def my_progress(self):
        exit_anim = Animation(opacity=0, duration=0.4)
        exit_anim2 = Animation(opacity=0, duration=0.4)

        # Start the exit animation for the buttons
        for child in self.menu_popup.content.children:
            exit_anim.start(child)
        exit_anim2.start(self.menu_popup)
        self.menu_popup.dismiss()

        # Get the absolute path to the "Graphics" folder
        graphics_folder = os.path.join(os.path.dirname(__file__), 'Graphics')
        menu_button_image_path = os.path.join(graphics_folder, 'menubutton.png')
        level_background_image_path = os.path.join(graphics_folder, 'gradient_background_v4.png')

        background_image = Image(source=level_background_image_path, size_hint=(1, 1), pos=(0, 0))
        self.layout.add_widget(background_image)

        percentages = calculate_hsk_completion()
        if percentages:
            # Create Labels for each HSK level's percentage
            labels = []
            for level, percentage in percentages.items():
                label = Label(
                    text=f"HSK {level}: {percentage}%",
                    size_hint=(None, None),
                    size=(300, 140),
                    color=(0, 0, 0, 1),
                    pos_hint={'center_x': 0.5, 'center_y': 0.98 - (level * 0.11)},  # Adjust vertical positions
                    font_name='Han',
                    font_size=40
                )
                labels.append(label)

            # Create the 'MENU' button
            go_back_button = Button(
                size_hint=(None, None),
                size=(200, 100),
                background_normal=menu_button_image_path,
                background_down=menu_button_image_path,
                pos_hint={'center_x': 0.5, 'center_y': 0.17},
            )
            go_back_button.bind(on_release=self.go_to_menu)

            for label in labels:
                self.layout.add_widget(label)

            self.layout.add_widget(go_back_button)

    def toggle_sound(self, instance):
        graphics_folder = os.path.join(os.path.dirname(__file__), 'Graphics')
        sound_on_button_image_path = os.path.join(graphics_folder, 'volumeOn.png')
        sound_off_button_image_path = os.path.join(graphics_folder, 'volumeOff.png')

        #print('Sound button works')
        self.count += 1
        AudioManager.toggle_sound()
        if AudioManager.active_sound:
            if AudioManager.active_sound.volume > 0:
                self.sound = True

            else:
                self.sound = False

        # Change color based on the state
        if self.sound:
            #print(self.count)
            if self.count % 2 != 0:
                self.sound_button.background_normal = sound_off_button_image_path

            else:
                self.sound_button.background_normal = sound_on_button_image_path


    def difficult_words(self, value):
        self.value = value
        self.difficult = True
        self.update_hsk(self.value)

    def update_hsk(self, value):
        # Update the HSK variable based on the button that is clicked
        self.hsk = value
        # print(f"HSK is now set to {self.hsk}")
        self.start_learning(None)

    def start_learning(self, widget):
        # Define the exit animation for the buttons
        exit_anim_menu = Animation(opacity=0, duration=1)
        exit_anim_layout = Animation(opacity=0, duration=1)
        exit_anim_layout.bind(on_complete=self.on_exit_animation_complete)

        # Start the exit animation for menu buttons
        for child in self.menu_popup.content.children:
            if child not in [self.layout, self.sound_button]:
                exit_anim_menu.start(child)


        layout_children = self.layout.children
        if len(layout_children) >= 3:

            exit_anim_layout.start(layout_children[-1])
            exit_anim_layout.start(layout_children[-2])
            exit_anim_layout.start(layout_children[-3])


        exit_anim_menu.start(self.menu_popup)
        self.menu_popup.dismiss()


    def on_exit_animation_complete(self, animation, widget):
        # Callback function when the exit animation is complete
        self.menu_popup.dismiss()  # Dismiss the menu popup
        self.create_flashcard_fold()
        self.flashcard_label = self.create_new_flashcard()
        self.layout.clear_widgets()
        self.layout.add_widget(self.flashcard_label)

    def quit_app(self, widget):
        MDApp.get_running_app().stop()

    def create_new_flashcard(self):
        if self.current_card_index < len(self.flashcards):
            card_data = self.flashcards[self.current_card_index]
            return Flashcard(chinese=card_data["chinese"], pinyin=card_data["pinyin"], english=card_data["english"], card_count=[self.card_count], fold_size = self.fold_size, hsk=[self.hsk])
        return None

    def create_flashcard_fold(self):
        if self.hsk == 1:
            hsk1_words = random.sample(self.get_hsk_words(1, 20), 20)
            self.flashcards = hsk1_words
            self.fold_size = len(self.flashcards)
            random.shuffle(self.flashcards)
        if self.hsk == 2:
            hsk1_words = random.sample(self.get_hsk_words(1, 5), 5)
            hsk2_words = random.sample(self.get_hsk_words(2, 15), 15)
            self.flashcards = hsk1_words + hsk2_words
            self.fold_size = len(self.flashcards)
            random.shuffle(self.flashcards)
        if self.hsk == 3:
            hsk1_words = random.sample(self.get_hsk_words(1, 3), 3)
            hsk2_words = random.sample(self.get_hsk_words(2, 5), 5)
            hsk3_words = random.sample(self.get_hsk_words(3, 12), 12)
            self.flashcards = hsk1_words + hsk2_words + hsk3_words
            self.fold_size = len(self.flashcards)
            random.shuffle(self.flashcards)
        if self.hsk == 4:
            hsk1_words = random.sample(self.get_hsk_words(1, 0), 0)
            hsk2_words = random.sample(self.get_hsk_words(2, 2), 2)
            hsk3_words = random.sample(self.get_hsk_words(3, 3), 3)
            hsk4_words = random.sample(self.get_hsk_words(4, 15), 15)
            self.flashcards = hsk1_words + hsk2_words + hsk3_words + hsk4_words
            self.fold_size = len(self.flashcards)
            random.shuffle(self.flashcards)
        if self.hsk == 5:
            hsk1_words = random.sample(self.get_hsk_words(1, 0), 0)
            hsk2_words = random.sample(self.get_hsk_words(2, 0), 0)
            hsk3_words = random.sample(self.get_hsk_words(3, 4), 4)
            hsk4_words = random.sample(self.get_hsk_words(4, 10), 10)
            hsk5_words = random.sample(self.get_hsk_words(5, 26), 26)
            self.flashcards = hsk1_words + hsk2_words + hsk3_words + hsk4_words + hsk5_words
            self.fold_size = len(self.flashcards)
            random.shuffle(self.flashcards)
        if self.hsk == 6:
            hsk1_words = random.sample(self.get_hsk_words(1, 0), 0)
            hsk2_words = random.sample(self.get_hsk_words(2, 0), 0)
            hsk3_words = random.sample(self.get_hsk_words(3, 0), 0)
            hsk4_words = random.sample(self.get_hsk_words(4, 4), 4)
            hsk5_words = random.sample(self.get_hsk_words(5, 10), 10)
            hsk6_words = random.sample(self.get_hsk_words(6, 26), 26)
            self.flashcards = hsk1_words + hsk2_words + hsk3_words + hsk4_words + hsk5_words + hsk6_words
            self.fold_size = len(self.flashcards)
            random.shuffle(self.flashcards)

    def get_hsk_words(self, hsk_level, number_cards):
        all_hsk_words = self.get_hsk_words_list()
        learned_words = set(self.learned_status_manager.get_learned_words())

        if self.difficult:
            unknown_words = [word for word in all_hsk_words if
                             word["hsk_level"] == hsk_level and word["chinese"] not in learned_words]

            if len(unknown_words) < number_cards:
                known_words = [word for word in all_hsk_words if
                               word["hsk_level"] == hsk_level and word["chinese"] in learned_words]
                known_words.sort(
                    key=lambda x: self.learned_status_manager.learned_status.get(x["chinese"], {}).get("value", float(
                        'inf')))  # Use "value" instead of "level"
                missing_words = known_words[:min(number_cards - len(unknown_words), len(known_words))] + unknown_words

                return missing_words

            else:
                return random.sample(unknown_words, min(number_cards, len(unknown_words)))

        else:
            return [word for word in all_hsk_words if word["hsk_level"] == hsk_level]

    def get_hsk_words_list(self):
        hsk_words = []
        flashcard_files = ["hsk1_vocabulary_only.csv", "hsk2_vocabulary_only.csv", "hsk3_vocabulary_only.csv", "hsk4_vocabulary_only.csv", "hsk5_vocabulary_only.csv", "hsk6_vocabulary_only.csv"]
        for file_name, hsk_level in zip(flashcard_files, [1, 2, 3, 4, 5, 6]):
            with open(file_name, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    hsk_words.append({
                        "chinese": row["Chinese"],
                        "pinyin": row["Pinyin"],
                        "english": row["English"],
                        "hsk_level": hsk_level
                    })
        return hsk_words

    def next_flashcard(self, direction):
        graphics_folder = os.path.join(os.path.dirname(__file__), 'Graphics')
        menu_button_image_path = os.path.join(graphics_folder, 'menubutton.png')
        restart_button_image_path = os.path.join(graphics_folder, 'restartbutton2.png')
        restart_back_image_path = os.path.join(graphics_folder, 'restartbutton2back.png')
        score_background_image_path = os.path.join(graphics_folder, 'gradient_background_v4.png')

        if not self.flashcards:
            score = self.calculate_score(self.swipe_count, self.good_flashcards)
            self.layout.clear_widgets()
            no_more_cards_label = Label(text=f"{score}%", font_size=120, color=(1, 1, 1, 1),outline_width = 3, outline_color=(0, 0, 0, 1),pos_hint={'center_x': 0.5, 'center_y': 0.5})
            no_more_cards_label.size = (250, 100)

            # Add the background image
            background_image = Image(source=score_background_image_path, size_hint=(1, 1), pos=(0, 0))
            self.layout.add_widget(background_image)

            restart_button = Button(
                size_hint=(None, None),
                size=(300,160),
                background_normal= restart_button_image_path,
                background_down=restart_back_image_path,
                pos_hint={'center_x': 0.5, 'center_y': 0.8},
            )
            restart_button.bind(on_release=self.restart_game)
            go_back_button = Button(
                size_hint=(None, None),
                size=(300,160),
                background_normal=menu_button_image_path,
                background_down=menu_button_image_path,
                pos_hint={'center_x': 0.5, 'center_y': 0.2},
            )
            go_back_button.bind(on_release=self.go_to_menu)


            self.layout.add_widget(no_more_cards_label)
            self.layout.add_widget(restart_button)
            self.layout.add_widget(go_back_button)

            self.game_ended = True  # Set the game_ended flag
        else:
            self.current_card_index += 1
            if self.current_card_index < len(self.flashcards):
                self.animate_flashcard_change(direction)
            else:
                self.current_card_index = 0
                self.animate_flashcard_change(direction)

    def animate_flashcard_change(self, direction):
        flashcard_label = self.flashcard_label
        animation = Animation(opacity=0, duration=0.4)

        if direction == "left":  # Good side
            tint_color = Color(0, 1, 0, 0.1)  # Green tint
            flashcard_label.canvas.before.add(tint_color)
            tint_rectangle = Rectangle(pos=(58,234), size=(334,334))
            flashcard_label.canvas.before.add(tint_rectangle)

        elif direction == "right":  # Bad side
            tint_color = Color(1, 0, 0, 0.1)  # Red tint
            flashcard_label.canvas.before.add(tint_color)
            tint_rectangle = Rectangle(pos=(58,234), size=(334,334))
            flashcard_label.canvas.before.add(tint_rectangle)

            # Slide the flashcard off the screen to the right
            animation &= Animation(x=self.layout.width, duration=0.5)

        animation.bind(on_complete=lambda *args: self.change_flashcard_text(direction))
        animation.start(flashcard_label)

    def change_flashcard_text(self, direction):
        flashcard_label = self.flashcard_label
        flashcard_label.opacity = 1
        flashcard_label.x = 0
        flashcard_label.is_flipped = False
        flashcard_label.chinese_label.text = ""
        flashcard_label.pinyin_label.text = ""
        flashcard_label.english_label.text = ""

        new_flashcard = self.create_new_flashcard()
        if new_flashcard:
            self.layout.remove_widget(flashcard_label)
            self.flashcard_label = new_flashcard
            self.layout.add_widget(self.flashcard_label)

    def calculate_score(self, swipes, good_flashcards):
        swipes = self.swipe_count
        fold_size = len(good_flashcards)
        score = 5 * (fold_size - (swipes - fold_size))
        if score < 0:
            score = 0

        # Update the user's score using the ScoreManager
        self.user_name = "Miguel"  # Replace with the actual user's name
        self.score_manager.write_scores(self.user_name, score)

        return score

    def restart_game(self, instance):
        self.layout.clear_widgets()  # Clear all widgets from the layout
        self.flashcards = []  # Clear the existing flashcards
        self.current_card_index = 0
        self.swipe_count = 0
        self.card_count = 1
        self.good_flashcards = []
        self.bad_flashcards = []

        self.create_flashcard_fold()  # Create a new set of flashcards

        # Re-add only the flashcard label
        self.flashcard_label = self.create_new_flashcard()
        self.layout.add_widget(self.flashcard_label)

    # Inside the FlashcardApp class

    def go_to_menu(self, instance):
        # Clear the current game interface
        self.layout.clear_widgets()
        self.flashcards = []
        self.current_card_index = 0
        self.swipe_count = 0
        self.card_count = 1
        self.good_flashcards = []
        self.bad_flashcards = []
        self.difficult = False


        menu_layout = RelativeLayout()

        # Get the absolute path to the "Graphics" folder
        graphics_folder = os.path.join(os.path.dirname(__file__), 'Graphics')

        # Get the absolute path to the image file
        image_path = os.path.join(graphics_folder, 'gradient_background_v4.png')

        hsk1_button_image_path = os.path.join(graphics_folder, 'HSK1.png')
        hsk1_back_image_path = os.path.join(graphics_folder, 'HSK1_back.png')
        hsk2_button_image_path = os.path.join(graphics_folder, 'HSK2.png')
        hsk2_back_image_path = os.path.join(graphics_folder, 'HSK2_back.png')
        hsk3_button_image_path = os.path.join(graphics_folder, 'HSK3.png')
        hsk3_back_image_path = os.path.join(graphics_folder, 'HSK3_back.png')
        hsk4_button_image_path = os.path.join(graphics_folder, 'HSK4.png')
        hsk4_back_image_path = os.path.join(graphics_folder, 'HSK4_back.png')
        hsk5_button_image_path = os.path.join(graphics_folder, 'HSK5.png')
        hsk5_back_image_path = os.path.join(graphics_folder, 'HSK5_back.png')
        hsk6_button_image_path = os.path.join(graphics_folder, 'HSK6.png')
        hsk6_back_image_path = os.path.join(graphics_folder, 'HSK6_back.png')
        lvl_button_image_path = os.path.join(graphics_folder, 'Levelbutton-v2.png')
        sound_on_button_image_path = os.path.join(graphics_folder, 'volumeOn.png')
        sound_off_button_image_path = os.path.join(graphics_folder, 'volumeOff.png')

        button_size = (170, 190)
        f_size = 50


        greeting_label = Label(
            text=f'你好',
            font_size=26,
            font_name = "Noto",
            color = (0,0,0,1),
            bold=True,
            pos=(-141, 324),
            halign='left'
        )

        greeting_label2 = Label(
            text=f'{self.user_name}',
            font_size=30,
            font_name = "Roboto",
            color = (0,0,0,1),
            bold=True,
            pos=(-118, 286),
            halign='left'
        )


        learn_button_1 = Button(
            size_hint=(None, None),
            font_size = f_size,
            size=button_size,
            background_normal = hsk1_button_image_path,
            background_down = hsk1_back_image_path,
            pos_hint={'center_x': (90/360)+0.02, 'center_y': ((640 / 1.3) / 640)-0.058},
        )

        learn_button_2 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal= hsk2_button_image_path,
            background_down = hsk2_back_image_path,
            pos_hint={'center_x': (270/360)-0.02, 'center_y': ((640 / 1.3) / 640)-0.058},
        )

        learn_button_3 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal = hsk3_button_image_path,
            background_down = hsk3_back_image_path,
            pos_hint={'center_x': (90/360)+0.02, 'center_y': ((640/2)/640)-0.062},
        )
        learn_button_4 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal = hsk4_button_image_path,
            background_down = hsk4_back_image_path,
            pos_hint={'center_x': (270/360)-0.02, 'center_y': ((640/2)/640)-0.062},
        )

        learn_button_5 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal = hsk5_button_image_path,
            background_down = hsk5_back_image_path,
            pos_hint={'center_x': (90/360)+0.02, 'center_y': ((640 / 4.4) / 640)-0.062},
        )
        learn_button_6 = Button(
            size_hint=(None, None),
            font_size=f_size,
            size=button_size,
            background_normal = hsk6_button_image_path,
            background_down = hsk6_back_image_path,
            pos_hint={'center_x': (270/360)-0.02, 'center_y': ((640 / 4.4) / 640)-0.062},
        )

        see_progress = Button(
            size_hint=(None, None),
            size=(120,82),
            font_size = 28,
            color =(0,0,0,1),
            background_normal='',  # Set background_normal to an empty string
            background_down='',  # Set background_down to an empty string
            background_color=(0, 0, 0, 0),
            pos_hint={'center_x': 0.76, 'center_y': 0.884},
        )

        see_progress2 = Button(
            size_hint=(None, None),
            size=(120,82),
            font_size = 15,
            color =(0,0,0,1),
            background_normal='',  # Set background_normal to an empty string
            background_down='',  # Set background_down to an empty string
            background_color=(0, 0, 0, 0),
            pos_hint={'center_x': 0.76, 'center_y': 0.932},
        )

        sound_button = Button(
            size_hint=(None, None),
            size=(76,76),
            background_normal=sound_on_button_image_path,
            background_down=sound_on_button_image_path,
            pos_hint={'center_x': 0.86, 'center_y': 0.995}
        )

        if self.count % 2 == 0:
            sound_button.background_normal = sound_on_button_image_path
        else:
            sound_button.background_normal = sound_off_button_image_path

        see_progress.font_name = "Noto"
        see_progress.text = f'[b][font=Roboto]LVL: {calculate_user_level()} [/font]级[/b]'
        see_progress.markup = True

        see_progress2.text = f'{self.learned_status_manager.get_learned_words_count()} words discovered\n{self.learned_status_manager.get_mastered_words_count()} words mastered'

        learn_button_1.bind(on_release=lambda instance: self.select_fold(1))
        learn_button_2.bind(on_release=lambda instance: self.select_fold(2))
        learn_button_3.bind(on_release=lambda instance: self.select_fold(3))
        learn_button_4.bind(on_release=lambda instance: self.select_fold(4))
        learn_button_5.bind(on_release=lambda instance: self.select_fold(5))
        learn_button_6.bind(on_release=lambda instance: self.select_fold(6))
        see_progress.bind(on_release=lambda instance: self.my_progress())
        see_progress2.bind(on_release=lambda instance: self.my_progress())
        sound_button.bind(on_release=self.toggle_sound)




        self.sound_button = sound_button



        menu_layout.add_widget(greeting_label)
        menu_layout.add_widget(greeting_label2)
        menu_layout.add_widget(learn_button_1)
        menu_layout.add_widget(learn_button_2)
        menu_layout.add_widget(learn_button_3)
        menu_layout.add_widget(learn_button_4)
        menu_layout.add_widget(learn_button_5)
        menu_layout.add_widget(learn_button_6)
        menu_layout.add_widget(see_progress)
        menu_layout.add_widget(see_progress2)
        menu_layout.add_widget(sound_button)


        # Create the Popup with the background image
        self.menu_popup = Popup(title="", content=menu_layout, size_hint=(1, 1), size=(900, 820),
                                auto_dismiss=True, background=image_path, separator_color=[1, 1, 1, 0])

        # Show the menu when the app starts
        self.menu_popup.open()


if __name__ == '__main__':
    FlashcardApp().run()

