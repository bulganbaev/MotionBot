import glob
import random
from threading import Thread
import cv2
import numpy as np
import os

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, Updater


class Face_recognizer(Thread):
    """Class dedicated to face recognition
    Each face is saved in a folder inside faces_dir with the following syntax s_idx_subjectName, where idx is the
    number of direcoties inside faces_dir and subjectName is the name of the person the face belogns to."""

    def __init__(self, disp):

        Thread.__init__(self)

        self.faces_dir = "Resources/Faces/"
        self.unknown = self.faces_dir + "Unknown/"


        #======RECOGNIZER VARIABLES======
        self.face_recognizer = cv2.face.createLBPHFaceRecognizer()
        self.is_training=False


        #======TELEGRAM VARIABLES========
        self.disp = disp

        # Creating conversation handler
        conversation = ConversationHandler(
            [CallbackQueryHandler(self.new_face, pattern="/unknown_new")],
            states={
                1: [MessageHandler(Filters.text, self.get_new_name)]

            },
            fallbacks=[CallbackQueryHandler(self.end_callback, pattern="/end")]
        )

        # Custom inlinekeyboard and start message
        self.classify_start_inline = InlineKeyboardMarkup([
            [InlineKeyboardButton("See Faces", callback_data="/classify_see"),
             InlineKeyboardButton("Save Faces", callback_data="/classify_save")],
            [InlineKeyboardButton("Exit", callback_data="/end")]])
        self.classify_start_msg = "Welcome, here you can choose what you want to do"

        # adding everything to the bot
        disp.add_handler(conversation)
        disp.add_handler(CallbackQueryHandler(self.see_faces, pattern="/classify_see"))
        disp.add_handler(CallbackQueryHandler(self.send_faces, pattern="/view_face"))
        disp.add_handler(CallbackQueryHandler(self.send_unknown_face, pattern="/classify_save"))
        disp.add_handler(CallbackQueryHandler(self.move_kwnown_face, pattern="/unknown_known"))
        disp.add_handler(CallbackQueryHandler(self.delete_unkwon_face, pattern="/unknown_del"))
        disp.add_handler(CommandHandler("classify", self.classify_start))
        disp.add_handler(CallbackQueryHandler(self.end_callback, pattern="/end"))

    def run(self):

        self.train_model()
        #updater.start_polling()
        while True:continue


    #===================TELEGRAM=========================



    def classify_start(self, bot, update):
        """Initial function for the classify stage"""

        update.message.reply_text(self.classify_start_msg, reply_markup=self.classify_start_inline)

    def see_faces(self, bot, update):
        """Function to choose what face the user want to see"""

        inline = self.generate_inline_keyboard("/view_face ")

        if not inline:
            self.back_to_start(bot, update, "Sorry... no saved faces were found")
            return

        to_send = "What face do you want to see?"

        bot.edit_message_text(
            chat_id=update.callback_query.message.chat_id,
            text=to_send,
            message_id=update.callback_query.message.message_id,
            parse_mode="HTML",
            reply_markup=inline
        )

    def send_faces(self, bot, update):
        """Function to send all the photo of a specific subdir"""

        # get the param
        s_name = update.callback_query.data.split()[1]
        user_id = update._effective_user.id

        # check if the name is in the faces dir
        dir_name = [elem for elem in os.listdir(self.faces_dir) if s_name in elem]
        if len(dir_name) == 0:
            self.back_to_start(bot, update, "Sorry no face found with name " + s_name)
            return

        # take the dir name
        dir_name = dir_name[0]+"/"
        # for every image in the dir
        for image in glob.glob(self.faces_dir + dir_name + '*.png'):
            # open the image and send it
            with open(image, "rb") as file:
                bot.sendPhoto(user_id, file)

        self.end_callback(bot, update)

        self.classify_start(bot, update.callback_query)

    def send_unknown_face(self, bot, update):
        """Function to send an unknown face (in the Unknown dir)"""

        to_choose=glob.glob(self.unknown + '*.png')

        if len(to_choose)==0:
            self.back_to_start(bot,update,"Sorry, no photos found")
            return

        image = random.choice(to_choose)
        user_id = update._effective_user.id

        inline = self.generate_inline_keyboard("/unknown_known " + image + " ",
                                               InlineKeyboardButton("New", callback_data="/unknown_new " + image),
                                               InlineKeyboardButton("Delete", callback_data="/unknown_del " + image),
                                               InlineKeyboardButton("Exit", callback_data="/end " + image))

        bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,

        )
        to_send="You can either choose one of the known faces, create a new one or delete the photo\nThere are currently " \
                ""+str(len(to_choose))+" photos to be classified"
        with open(image, "rb") as file:
            bot.sendPhoto(user_id, file,
                          caption=to_send,
                          reply_markup=inline)

    def move_kwnown_face(self, bot, update):
        """Function to move a known face from Unknown dir to face_dir"""

        # the param has the format:  image_name dir_name
        param = update.callback_query.data.split()
        image_name = param[1]
        dir_name = param[2]

        # get the length of the images in the directory
        dir_name=self.faces_dir+self.get_name_dir(dir_name)+"/"
        idx = len([name for name in os.listdir( dir_name)])
        #generate new image name
        new_image_name=dir_name+"image_"+str(idx)+".png"

        # delete the photo message
        self.end_callback(bot, update)

        # move the image
        try:
            os.rename(image_name,new_image_name)
        except FileNotFoundError:
            update.callback_query.message.reply_text("Photo not found")


        self.classify_start(bot,update.callback_query)

    def delete_unkwon_face(self, bot, update):
        """Function to delete a photo from the unknown dir"""
        image = update.callback_query.data.split()[1]
        self.end_callback(bot, update)

        try:
            os.remove(image)
        except FileNotFoundError:
            update.callback_query.message.reply_text("Photo not found!")
            return


        update.callback_query.message.reply_text("Photo deleted")

        self.classify_start(bot,update.callback_query)

    def new_face(self, bot, update):
        """Function to ask the user the name of the new subject"""

        image = update.callback_query.data.split()[1]

        to_send = "Please insert the subject name right after the image name. Like the following format : " \
                  "\n" + image + " subject_name\nYou have just one chance so be careful"


        bot.edit_message_caption(
            chat_id=update.callback_query.message.chat_id,
            caption=to_send,
            message_id=update.callback_query.message.message_id,
            parse_mode="HTML")
        update.callback_query.message.reply_text("<code>"+image+"</code>",parse_mode="HTML")


        return 1

    def get_new_name(self, bot, update):
        """Function to get a user name and create a folder"""
        param = update.message.text.split(" ")

        try:
            image_name = param[0]
            face_name = param[1]
        except IndexError:
            update.message.reply_text("I told you to be carefull!")
            return ConversationHandler.END

        if glob.glob(self.faces_dir+"*_"+face_name):
            update.message.reply_text("You cannot use the same name for two faces")
            return ConversationHandler.END

        self.add_image_move(self.unknown, image_name, face_name)
        update.message.reply_text("Done! You can now check the image under " + face_name)

        self.classify_start(bot,update)
        return ConversationHandler.END

    def back_to_start(self, bot, update, msg):

        bot.edit_message_text(
            chat_id=update.callback_query.message.chat_id,
            text=msg,
            message_id=update.callback_query.message.message_id,
            parse_mode="HTML",
            reply_markup=self.classify_start_inline
        )

    def end_callback(self, bot, update):

        bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,

        )


    #===================RECOGNIZER=========================

    def train_model(self):
        """Function to train the recognizer"""

        print("Training model...")
        #flag value
        self.is_training=True


        #prepare the data
        faces,labels=self.prepare_training_data()
        # train
        self.face_recognizer.train(faces, np.array(labels))


        self.is_training=False
        print("....Model trained")


    def predict(self, img):
        """ this function recognizes the person in image passed and draws a
        rectangle around detected face with name of the subject"""

        print("Predicting....")
        #do not try to predict while the model is training
        if self.is_training:
            return False

        if len(img)==0:
            print("No image for prediction")
            return False

        #convert to right unit type and turn image to grayscale
        img = np.array(img, dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # predict the image using our face recognizer
        #collect = cv2.face.StandardCollector_create()
        label=self.face_recognizer.predict(gray)
        print(label)
        #print(collect,collect.getResults())
        # get name of respective label returned by face recognizer
        label_text = self.name_from_label(label)

        print("...Done")
        return label_text

    #===================UTILS=========================

    def name_from_label(self, label):
        """Function to get the person name by the label"""

        #take all the direcories
        dirs = glob.glob(self.faces_dir + "s_"+str(label)+"_*")

        # if there are none return false
        if len(dirs)==0: return False
        else:dirs=dirs[0]

        #get the name

        return dirs.split("_")[-1]



    def prepare_training_data(self):

        # ------STEP-1--------
        # get the directories (one directory for each subject) in data folder
        dirs = glob.glob(self.faces_dir + "s_*")

        # list to hold all subject faces
        faces = []
        # list to hold labels for all subjects
        labels = []

        # let's go through each directory and read images within it
        for dir_name in dirs:
            # get the subject label (number)
            label = int(dir_name.split("/")[2].split("_")[1])

            #for every image in the direcotry append image,label
            for image_path in glob.glob(dir_name + "/*.png"):
                image = cv2.imread(image_path)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces.append(gray)
                labels.append(label)

        return faces, labels


    def generate_inline_keyboard(self, callback_data, *args):

        # get all the saved subjects names
        names = self.get_dir_subjects()

        # uf there are none return
        if len(names) == 0 and len(args)==0:
            return False

        # add the names to the inline button
        rows = []
        cols = []

        for name in names:

            # only three cols allowed
            if len(cols) == 3:
                rows.append(cols)
                del cols[:]
            # add the buttom to the row
            cols.append(InlineKeyboardButton(name, callback_data=callback_data + name))

        #if there was less than three faces append them
        if not rows: rows.append(cols)

        #if there are other buttons from args, append them
        if args: rows.append(args)

        inline = InlineKeyboardMarkup(rows)

        return inline

    def add_image_write(self, image_list, subject_name=""):

        #currently used only for the unknown direcotry
        subject_name="Unknown"

        print("Adding face images to unknown folder...")


        # look for the direcotry and create it if not present
        if not glob.glob(self.faces_dir+subject_name):
            return False
            #self.add_folder(subject_name)

        # get the directory name
        dir = self.get_name_dir(subject_name)

        if not dir:
            return False
        else:
            dir = self.faces_dir + dir + "/"

        # get the length of the images in the directory
        idx = len([name for name in os.listdir(dir) if os.path.isfile(name)])

        for image in image_list:
            image_name = dir + "image_" + str(idx) + ".png"
            cv2.imwrite(image_name, image)
            idx+=1

        print("...Done")


        return True

    def add_image_move(self, from_path, image, subject_name):

        # look for the direcotry and create it if not present
        if not subject_name in os.listdir(self.faces_dir):
            self.add_folder(subject_name)

        # get the directory name
        dir = self.get_name_dir(subject_name)

        if not dir: return False
        else: dir=self.faces_dir+dir+"/"

        # get the length of the images in the directory
        idx = len([name for name in os.listdir(dir) if os.path.isfile(name)])

        image_name = dir + "image_" + str(idx) + ".png"

        os.rename(image, image_name)

        return True

    def add_folder(self, name):
        """Create a folder for the new person"""

        if not name in os.listdir(self.faces_dir):
            # get how many folder there are in the faces dir
            idx = len(glob.glob(self.faces_dir + 's_*'))
            # generate the name
            name = "s_" + str(idx) + "_" + name
            # create the directory
            os.makedirs(self.faces_dir + name)

    def get_name_dir(self, subject_name):

        for dir in os.listdir(self.faces_dir):
            if subject_name in dir:
                return dir

        return False

    def get_dir_subjects(self):
        """Function to get all the names saved in the faces direcotry"""

        s_names = []

        import glob
        for name in glob.glob(self.faces_dir + 's_*'):
            s_names.append(name.split("_")[2])

        return s_names


# updater = Updater("")
# disp = updater.dispatcher
# #
# face=Face_recognizer(disp)
# face.start()