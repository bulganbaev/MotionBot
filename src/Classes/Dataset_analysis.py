import os

import face_recognition
from face_recognition.face_detection_cli import image_files_in_folder
from sklearn import preprocessing, neighbors
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from Path import Path as pt
from mpl_toolkits.mplot3d import Axes3D

from Utils.serialization import load_pkl, dump_pkl


class DataAnalysis():

    def __init__(self, x, y):

        self.x = x
        self.y = y

    def set_data(self, x, y):

        self.x = x
        self.y = y

    def knn_analysis(self, projected, encoded, n_neighbors=None):

        def accuracy_knn(x, y):
            X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.33, random_state=42)
            clf = neighbors.KNeighborsClassifier(n_neighbors, weights=weights)
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            return round(accuracy_score(y_test, y_pred) * 100, 2)

        if n_neighbors is None:
            n_neighbors = int(round(np.math.sqrt(len(projected))))

        projected = projected[:, :2]
        print("Chose n_neighbors automatically:", n_neighbors)
        X_train, X_test, y_train, y_test = train_test_split(projected, encoded, test_size=0.33, random_state=42)
        h = .02  # step size in the mesh
        for weights in ['uniform', 'distance']:
            # we create an instance of Neighbours Classifier and fit the data.
            clf = neighbors.KNeighborsClassifier(n_neighbors, weights=weights)
            clf.fit(X_train, y_train)

            # Plot the decision boundary. For that, we will assign a color to each
            # point in the mesh [x_min, x_max]x[y_min, y_max].
            x_min, x_max = X_train[:, 0].min() - 0.05, X_train[:, 0].max() + 0.05
            y_min, y_max = X_train[:, 1].min() - 0.05, X_train[:, 1].max() + 0.05
            xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                                 np.arange(y_min, y_max, h))

            Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])

            # Put the result into a color plot
            Z = Z.reshape(xx.shape)
            plt.figure()
            plt.pcolormesh(xx, yy, Z, cmap="viridis")

            accuracy = accuracy_knn(self.x, encoded)

            # Plot also the training points
            plt.scatter(X_train[:, 0], X_train[:, 1], c=y_train, cmap="viridis",
                        edgecolor='k', s=20)
            plt.xlim(xx.min(), xx.max())
            plt.ylim(yy.min(), yy.max())
            plt.title("3-Class classification (k = %i, weights = '%s', accuracy = %d)"
                      % (n_neighbors, weights, accuracy))

            plt.savefig(pt.join(pt.ANALISYS_DIR, f"knn_{weights}"))
            plt.clf()

    def pca_analysis(self, encoded_label):
        pca = PCA()
        projected = pca.fit_transform(self.x, self.y)

        plt.plot(np.cumsum(pca.explained_variance_ratio_))
        plt.xlabel('number of components')
        plt.ylabel('cumulative explained variance')

        plt.savefig(pt.join(pt.ANALISYS_DIR, "variance_components"))

        plt.clf()
        fig = plt.figure()
        ax = Axes3D(fig)

        ax.scatter(projected[:, 0], projected[:, 1], projected[:, 2],
                   c=encoded_label, edgecolor='red', alpha=0.5, s=30,
                   cmap=plt.cm.get_cmap('viridis', 10))

        plt.savefig(pt.join(pt.ANALISYS_DIR, "3d_plot"))

        plt.clf()

        plt.scatter(projected[:, 0], projected[:, 1],
                    c=encoded_label, edgecolor='none', alpha=0.5,
                    cmap=plt.cm.get_cmap('viridis', 10))
        plt.xlabel('component 1')
        plt.ylabel('component 2')
        plt.colorbar()
        plt.savefig(pt.join(pt.ANALISYS_DIR, "2d_plot"))

        plt.clf()

        return projected

    def analyze(self):
        enc = preprocessing.LabelEncoder()
        encoded_label = enc.fit_transform(self.y)
        print("Executin PCA")
        projected = self.pca_analysis(encoded_label)
        print("Executing KNN")
        self.knn_analysis(projected, encoded_label)


def build_dataset_analysis():
    """
    build the dataset
    :return: X,Y as numpy arrays
    """
    x = []
    y = []

    # Loop through each person in the training set
    for class_dir in os.listdir(pt.FACES_DIR):
        if not os.path.isdir(os.path.join(pt.FACES_DIR, class_dir)) or "Unknown" in class_dir:
            continue

        # save directory
        subject_dir = os.path.join(pt.FACES_DIR, class_dir)

        # load encodings
        encodings = load_pkl(pt.join(subject_dir, pt.encodings))
        if encodings is None:
            encodings = []

        # Loop through each training image for the current person
        errors = 0
        for img_path in image_files_in_folder(subject_dir):
            image = face_recognition.load_image_file(img_path)
            os.remove(img_path)

            # take the bounding boxes an the image size
            face_bounding_boxes = 0, image.shape[1], image.shape[0], 0
            face_bounding_boxes = [face_bounding_boxes]

            try:
                encode = \
                    face_recognition.face_encodings(image, known_face_locations=face_bounding_boxes, num_jitters=10)[0]

                encodings.append(encode)

            except IndexError:
                print(f"out of range error number {errors}")
                errors += 1
                pass

        # save encodings
        dump_pkl(encodings, pt.join(subject_dir, pt.encodings))
        print(f"Encodings for {subject_dir} are {len(encodings)}")
        # update model
        x += encodings
        y += len(encodings) * [class_dir.split("_")[-1]]

    x = np.asarray(x)
    y = np.asarray(y)

    return x, y


if __name__ == '__main__':
    x, y = build_dataset_analysis()
    analysis = DataAnalysis(x, y)
    analysis.analyze()