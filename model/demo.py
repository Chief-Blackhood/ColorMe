# import the necessary packages
import os
import random

import cv2 as cv
import keras.backend as K
import numpy as np
import sklearn.neighbors as nn

from config import IMG_ROWS, IMG_COLS
from config import NB_NEIGHBORS, T, EPSILON
from model import build_model

if __name__ == '__main__':
    channel = 3

    model_weights_path = 'models/Imagnet_model.hdf5'
    model = build_model()
    model.load_weights(model_weights_path)

    print(model.summary())

    image_folder = './images/imagenette'
    names_file = 'valid_names.txt'
    with open(names_file, 'r') as f:
        names = f.read().splitlines()

    # samples = random.sample(names, 10)
    samples = [
        'test.jpg',
        'test2.jpg',
        'test3.jpg',
        'test4.jpg',
        'test5.jpg',
        'test6.jpg',
        'test7.jpg',
        'test8.jpg',
        'test9.jpg',
        'test10.jpg',
        'test11.jpeg',
        'test12.png',
        'test13.png',
        'test14.png',
        'test15.png',
        'test16.png',
        'test17.png',
        'test18.png',
        'test19.png',
        'test20.png',
        'test21.png',
        'test22.png',
        'test23.png',
    ]

    h, w = IMG_ROWS // 4, IMG_COLS // 4

    # Load the array of quantized ab value
    q_ab = np.load("data/pts_in_lab_space.npy")
    nb_q = q_ab.shape[0]

    # Fit a NN to q_ab
    nn_finder = nn.NearestNeighbors(n_neighbors=NB_NEIGHBORS, algorithm='ball_tree').fit(q_ab)

    for i in range(len(samples)):
        image_name = samples[i]
        # filename = samples[i]
        filename = os.path.join(image_folder, image_name)
        print('Start processing image: {}'.format(filename))
        # b: 0 <=b<=255, g: 0 <=g<=255, r: 0 <=r<=255.
        bgr = cv.imread(filename)
        gray = cv.imread(filename, 0)
        bgr = cv.resize(bgr, (IMG_ROWS, IMG_COLS), cv.INTER_CUBIC)
        gray = cv.resize(gray, (IMG_ROWS, IMG_COLS), cv.INTER_CUBIC)
        # L: 0 <=L<= 255, a: 42 <=a<= 226, b: 20 <=b<= 223.
        lab = cv.cvtColor(bgr, cv.COLOR_BGR2LAB)
        L = lab[:, :, 0]
        a = lab[:, :, 1]
        b = lab[:, :, 2]
        # print('np.max(L): ' + str(np.max(L)))
        # print('np.min(L): ' + str(np.min(L)))
        # print('np.max(a): ' + str(np.max(a)))
        # print('np.min(a): ' + str(np.min(a)))
        # print('np.max(b): ' + str(np.max(b)))
        # print('np.min(b): ' + str(np.min(b)))
        x_test = np.empty((1, IMG_ROWS, IMG_COLS, 1), dtype=np.float32)
        x_test[0, :, :, 0] = gray / 255.

        # L: 0 <=L<= 255, a: 42 <=a<= 226, b: 20 <=b<= 223.
        X_colorized = model.predict(x_test)
        X_colorized = X_colorized.reshape((h * w, nb_q))

        # Reweight probas
        X_colorized = np.exp(np.log(X_colorized + EPSILON) / T)
        X_colorized = X_colorized / np.sum(X_colorized, 1)[:, np.newaxis]

        # Reweighted
        q_a = q_ab[:, 0].reshape((1, 313))
        q_b = q_ab[:, 1].reshape((1, 313))

        X_a = np.sum(X_colorized * q_a, 1).reshape((h, w))
        X_b = np.sum(X_colorized * q_b, 1).reshape((h, w))
        # print('np.max(X_a): ' + str(np.max(X_a)))
        # print('np.min(X_a): ' + str(np.min(X_a)))
        # print('np.max(X_b): ' + str(np.max(X_b)))
        # print('np.min(X_b): ' + str(np.min(X_b)))
        X_a = cv.resize(X_a, (IMG_ROWS, IMG_COLS), cv.INTER_CUBIC)
        X_b = cv.resize(X_b, (IMG_ROWS, IMG_COLS), cv.INTER_CUBIC)

        # Before: -90 <=a<= 100, -110 <=b<= 110
        # After: 38 <=a<= 228, 18 <=b<= 238
        X_a = X_a + 128
        X_b = X_b + 128
        # print('np.max(X_a): ' + str(np.max(X_a)))
        # print('np.min(X_a): ' + str(np.min(X_a)))
        # print('np.max(X_b): ' + str(np.max(X_b)))
        # print('np.min(X_b): ' + str(np.min(X_b)))

        out_lab = np.zeros((IMG_ROWS, IMG_COLS, 3), dtype=np.int32)
        out_lab[:, :, 0] = lab[:, :, 0]
        out_lab[:, :, 1] = X_a
        out_lab[:, :, 2] = X_b
        out_L = out_lab[:, :, 0]
        out_a = out_lab[:, :, 1]
        out_b = out_lab[:, :, 2]
        # print('np.max(out_L): ' + str(np.max(out_L)))
        # print('np.min(out_L): ' + str(np.min(out_L)))
        # print('np.max(out_a): ' + str(np.max(out_a)))
        # print('np.min(out_a): ' + str(np.min(out_a)))
        # print('np.max(out_b): ' + str(np.max(out_b)))
        # print('np.min(out_b): ' + str(np.min(out_b)))
        out_lab = out_lab.astype(np.uint8)
        out_bgr = cv.cvtColor(out_lab, cv.COLOR_LAB2BGR)
        # print('np.max(out_bgr): ' + str(np.max(out_bgr)))
        # print('np.min(out_bgr): ' + str(np.min(out_bgr)))
        out_bgr = out_bgr.astype(np.uint8)

        if not os.path.exists('images_to_reach'):
            os.makedirs('images_to_reach')

        cv.imwrite('images_to_reach/{}_image.png'.format(i), gray)
        cv.imwrite('images_to_reach/{}_gt.png'.format(i), bgr)
        cv.imwrite('images_to_reach/{}_out.png'.format(i), out_bgr)

    K.clear_session()
