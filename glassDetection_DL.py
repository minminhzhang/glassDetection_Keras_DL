# -*- coding: utf-8 -*-
"""glassDetection_DL.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ky4_5bbqiFlhlUvDIgZ34jRON2f2YKAx
"""

from google.colab import drive
drive.mount('/content/gdrive')

import PIL.ImageOps
from PIL import Image
from sklearn import preprocessing
import numpy as np
import tensorflow as tf
import keras
from keras.utils.np_utils import to_categorical
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from tensorflow.keras import layers
import math
import random

def process_img(dataloc,datainfo):
    try:
        data = np.load("/content/gdrive/MyDrive/8920/Celeb60.npz")
        labels = data['labels']
        image_total = data['imageNames']
        imageData = data['imageData']
    except FileNotFoundError:
        loc = 0
        wglass_labels = []
        wglass_images = []
        noglass_labels = []
        noglass_images = []

        for line in open(datainfo): 
            loc = loc + 1
            if(loc == 1):
                length = int(line)
            elif(loc > 2):
                lineData = line.split(" ")
                lineData = list(filter(None, lineData))
                lineData[-1] = lineData[-1].strip()
                if(int(lineData[16])==1):
                    wglass_labels.append(1)
                    wglass_images.append(lineData[0])

        glass_num = len(wglass_images)
        noglass_num = 60000 - len(wglass_images)

        #get noglass images
        loc = 0
        for line in open(datainfo): 
            loc = loc + 1
            if(loc == 1):
                length = int(line)
            elif(loc > 2):
                lineData = line.split(" ")
                lineData = list(filter(None, lineData))
                lineData[-1] = lineData[-1].strip()
                if(int(lineData[16])==-1):
                    if(len(noglass_labels) == noglass_num):
                        break
                    noglass_labels.append(0)
                    noglass_images.append(lineData[0])

        #Get total data
        label_total = wglass_labels + noglass_labels
        image_total = wglass_images + noglass_images

        tmp = list(zip(label_total, image_total))
        random.shuffle(tmp)
        label_total, image_total = zip(*tmp)

        imageData = np.zeros((60000,148,148,3), dtype=np.uint8)
#         imageData = []
        index = 0
        for images in image_total:
            dataloc = dataloc + images
            print(index, dataloc)
            image = Image.open(dataloc)
#             image = image.convert('L')
            image = image.resize((148, 148), Image.BICUBIC)
            
            image_array = np.asarray(image)
            # print("!!")
            # print(image_array.shape)
            imageData[i,:,:,:] = image_array
            index = index + 1
        
        label_total = np.asarray(label_total)
        labels = np.zeros((len(label_total),1), dtype=np.int)
        labels[:,0] = label_total
        image_total = np.asarray(image_total)

        np.savez("Celeb60.npz", imageNames=image_total, labels=labels, imageData=imageData)
    return(imageData, labels, image_total)

datainfo = '/content/gdrive/MyDrive/8920/data/CelebA/Anno/list_attr_celeba.txt'
dataloc = '/content/gdrive/MyDrive/8920/data/CelebA/Img/img_align_celeba/'
celebData = 0
(celebData, labels, imageNames) = process_img(dataloc, datainfo)

image = keras.preprocessing.image.array_to_img(celebData[0])
print(image)
display(image)

#80% of 60000
# train_size = 38400 
# val_size = 9600
train_size = 33600 
val_size = 14400
test_size = 12000

x_train = celebData[0:train_size,:,:]
y_train = labels[0:train_size,:]

x_val = celebData[train_size:train_size+val_size,:,:]
y_val = labels[train_size:train_size+val_size,:]

x_test = celebData[train_size+val_size:train_size+val_size+test_size,:,:]
y_test = labels[train_size+val_size:train_size+val_size+test_size,:]


x_train = x_train.reshape(train_size, 148, 148, 3)
x_val = x_val.reshape(val_size,148, 148, 3)
x_test = x_test.reshape(test_size,148, 148, 3)
y_val = to_categorical(y_val,2)
y_val = to_categorical(y_val,2)
y_test = to_categorical(y_test,2)

# def cnn_model_fn(features, labels, mode):
input_layer = keras.Input(shape=(148,148,3))
c1 = layers.Conv2D(96, kernel_size=[5, 5], padding="same", activation=tf.nn.relu)(input_layer)
pool1 = layers.MaxPooling2D(pool_size=[5, 5], strides=2)(c1)
c2 = layers.Conv2D(265, kernel_size=[5, 5], strides=1, padding="valid", activation=tf.nn.relu)(pool1)
pool2 = layers.MaxPooling2D(pool_size=[3, 3], strides=3)(c2)
c3 = layers.Conv2D(384, kernel_size=[3, 3], strides=1, padding="valid", activation=tf.nn.relu)(pool2)
c4 = layers.Conv2D(384, kernel_size=[3, 3], strides=1, padding="valid", activation=tf.nn.relu)(c3)
c5 = layers.Conv2D(256, kernel_size=[3, 3], strides=1, padding="valid", activation=tf.nn.relu)(c4)
pool3 = layers.MaxPooling2D(pool_size=[2, 2], strides=3)(c5)
flatten = layers.Flatten()(pool3)
dense1 = layers.Dense(4096, activation=tf.nn.relu)(flatten)
dropout1 = layers.Dropout(rate=0.4)(dense1)
dense2 = layers.Dense(4096, activation=tf.nn.relu)(dropout1)
dropout2 = layers.Dropout(rate=0.4)(dense2)
output_layer = layers.Dense(2, activation='softmax')(dropout2)

model = keras.Model(inputs=input_layer, outputs=output_layer, name='glassDetection_model')
model.summary()

model.compile(loss=keras.losses.CategoricalCrossentropy(from_logits=True), optimizer='adam', metrics=['accuracy'])

callback = tf.keras.callbacks.EarlyStopping(monitor='loss', min_delta=0.02, patience=3)

# hist = model.fit(x=x_train,y=train_images_labels, epochs=30, batch_size=128, validation_data=(x_val, y_val), callbacks=[callback], verbose=1)
hist = model.fit(x=x_train,y=y_val, epochs=15, batch_size=128, validation_data=(x_val, y_val), verbose=1)

test_score = model.evaluate(x_test, y_test)
print("Test loss {:.4f}, accuracy {:.2f}%".format(test_score[0],test_score[1]*100))

f, ax = plt.subplots()
ax.plot([None] + hist.history['accuracy'], 'o-')
ax.plot([None] + hist.history['val_accuracy'], 'x-')
#Without log value
ax.legend(['Train accuracy', 'Validation accuracy'], loc = 0)
ax.set_title('eyeglass_detection_model Training/Validation accuracy per Epoch')
ax.set_xlabel('Epoch')
ax.set_ylabel('Accuracy')

from math import log

print([log(x) for x in hist.history['accuracy']])
#Log value
f, ax = plt.subplots()
ax.plot([None] + [log(x) for x in hist.history['accuracy']], 'o-')
ax.plot([None] + [log(x) for x in hist.history['val_accuracy']], 'x-')

ax.legend(['Train accuracy', 'Validation accuracy'], loc = 0)
ax.set_title('eyeglass_detection_model Training/Validation accuracy per Epoch')
ax.set_xlabel('Epoch')
ax.set_ylabel('Log accuracy')

f, ax = plt.subplots()
ax.plot([None] + hist.history['loss'], 'o-')
ax.plot([None] + hist.history['val_loss'], 'x-')

ax.legend(['Train loss', 'Validation loss'], loc = 0)
ax.set_title('eyeglass_detection_model Training/Validation Loss per Epoch')
ax.set_xlabel('Epoch')
ax.set_ylabel('Loss')

from keras.applications import mobilenet_v2
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
import tensorflow_datasets as tfds
import tensorflow as tf
from numpy import expand_dims

# print(model.input_shape)
dims = model.input_shape[1:3]
# print(dims)

#Get sample images from current path 
test_samples = ['0-1.jpg', '0-2.jpg','0-3.jpg', '0-4.jpg', '1-1.jpg', '1-2.jpg', \
                '1-3.jpg', '1-4.jpg', '1-5.jpg', '1-6.jpg', '1-7.jpg', '0-5.jpg', '0-6.jpg', '1-8.jpg', '0-7.jpg','0-8.jpg']
samples_init = []
samples_to_predict = []
for sample in test_samples:
    samples_init.append(keras.preprocessing.image.load_img(sample))
    im = keras.preprocessing.image.load_img(sample, target_size=dims)

    im = np.asarray(im)      
    samples_to_predict.append(im)
    
samples_to_predict = np.array(samples_to_predict)
# Generate predictions
predictions = model.predict(samples_to_predict)

# Get predictions
classes = np.argmax(predictions, axis = 1)
# print(classes)
predictions = []
for c in classes:
    if c == 0:
        predictions.append('No glasses')
    else:
        predictions.append('Glasses')
     
print('Results for prediction:') 
# plot results 
f, a = plt.subplots(4, 4)
f.set_size_inches(12, 12)
index = 0
for i in range(4):
    for j in range(4):
        img = samples_init[index]
        a[i][j].set_axis_off()
        a[i][j].set_title(predictions[index], fontsize=14)
        a[i][j].imshow(img)
        index += 1
plt.show()



for layer in model.layers:
	# check for convolutional layer
	if 'conv' not in layer.name:
		continue
	# get filter weights
	filters, biases = layer.get_weights()
	print(layer.name, filters.shape)

im = Image.open('1-1.jpg')
# print(type(im))
display(im)
model_sub = tf.keras.Model(inputs=model.inputs, outputs=model.layers[6].output)
# load the image from current path
img = load_img('1-1.jpg', target_size=(148, 148))
img = img_to_array(img)
img = expand_dims(img, axis=0)
img = preprocess_input(img)
# get feature map
feature_maps = model_sub.predict(img)
# plot first 16 feature maps
square = 4
ix = 1
for _ in range(square):
	for _ in range(square):
		ax = plt.subplot(square, square, ix)
		ax.set_xticks([])
		ax.set_yticks([])
		# plot filter channel in grayscale
		plt.imshow(feature_maps[0, :, :, ix-1], cmap='gray')
		ix += 1
plt.show()
