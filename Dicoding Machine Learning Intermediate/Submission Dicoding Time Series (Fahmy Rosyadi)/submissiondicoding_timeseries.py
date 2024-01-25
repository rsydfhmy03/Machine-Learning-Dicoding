# -*- coding: utf-8 -*-
"""SubmissionDicoding_TimeSeries.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oycoz4j-oMNLMRxa4JNHIOmatl3lRwIQ

# __DICODING MACHINE LEARNING__
Nama : Fahmy Rosyadi <br>
Asal Instansi : Politeknik Negeri Jember
<br>
Proyek : Temperature Prediction Time Series
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from keras.layers import Input, LSTM, Bidirectional, SpatialDropout1D, Dropout, Flatten, Dense, Embedding, BatchNormalization
from keras.models import Model
from keras.callbacks import EarlyStopping
from keras.preprocessing.text import Tokenizer, text_to_word_sequence
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.losses import CategoricalCrossentropy
from keras.optimizers import Adam
import matplotlib.pyplot as plt
import datetime
from sklearn.model_selection import train_test_split

"""## Load Dataset CSV dari Google Drive"""

from google.colab import drive
drive.mount('/content/drive')

"""Dataset : https://www.kaggle.com/datasets/berkeleyearth/climate-change-earth-surface-temperature-data?select=GlobalLandTemperaturesByMajorCity.csv"""

df = pd.read_csv('/content/drive/MyDrive/DatasetCollab/TimeSeries/GlobalLandTemperaturesByMajorCity.csv')
df

"""## Lakukan Preprocessing Data"""

df.drop(['City','Latitude','Longitude'], axis=1, inplace=True)
display(df)

df = df.loc[df['Country'].isin(['China'])]
df

df.info()

df['dt'] = pd.to_datetime(df['dt'], errors='coerce')
get_data = (df['dt'] > '1900-01-01') & (df['dt'] <= '2013-09-01')
df.loc[get_data]

df = df.loc[get_data].copy()
df.info()

df.drop(['Country'], axis=1, inplace=True)
df.reset_index(drop=True)

df.isnull().sum()

df['dt'].head()
df['AverageTemperature'].fillna(df['AverageTemperature'].mean(), inplace=True)
df['AverageTemperatureUncertainty'].fillna(df['AverageTemperatureUncertainty'].mean(), inplace=True)
df = df[['dt','AverageTemperature', 'AverageTemperatureUncertainty']]
df.head()

df.isnull().sum()

df_plot = df
df_plot[df_plot.columns.to_list()].plot(subplots=True, figsize=(15, 9))
plt.show()

dates = df['dt'].values
temp = df['AverageTemperature'].values

dates = np.array(dates)
temp = np.array(temp)

plt.figure(figsize=(15,9))
plt.plot(dates, temp)

plt.title('Average Temperature', fontsize = 20)
plt.ylabel('Temperature')
plt.xlabel('Datetime')

df.dtypes

"""## Split data train dan testing"""

x_train, x_test, y_train, y_test = train_test_split(temp, dates, test_size = 0.2, random_state = 0 , shuffle=False)
print('Total Data Train : ',len(x_train),'Total Data Test : ', len(x_test))

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
  series = tf.expand_dims(series, axis=-1)
  ds = tf.data.Dataset.from_tensor_slices(series)
  ds = ds.window(window_size + 1, shift=1, drop_remainder = True)
  ds = ds.flat_map(lambda w: w.batch(window_size + 1))
  ds = ds.shuffle(shuffle_buffer)
  ds = ds.map(lambda w: (w[:-1], w[-1:]))
  return ds.batch(batch_size).prefetch(1)

"""## Pelatihan Model"""

tf.keras.backend.set_floatx('float64')
w_z = 64
b_z = 250
s_b = 1000
train_set = windowed_dataset(x_train, window_size=w_z, batch_size=b_z, shuffle_buffer=s_b)
val_set = windowed_dataset(x_test, window_size=w_z, batch_size=b_z, shuffle_buffer=s_b)

model = tf.keras.models.Sequential([
    tf.keras.layers.Conv1D(filters=32, kernel_size=5,
                      strides=1, padding="causal",
                      activation="relu",
                      input_shape=[None, 1]),
    Bidirectional(LSTM(60, return_sequences=True)),
    Bidirectional(LSTM(60)),
    Dense(30, activation="relu"),
    Dense(10, activation="relu"),
    Dense(1),
])

model.summary()

Mae = (df['AverageTemperature'].max() - df['AverageTemperature'].min()) * 10/100
print(Mae)

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae')<5 and logs.get('val_mae')<5):
      print("\nMAE dari model < 10% skala data")
      self.model.stop_training = True
callbacks = myCallback()

optimizer = tf.keras.optimizers.SGD(lr=1.0000e-04, momentum=0.9)

model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])

history = model.fit(train_set, epochs=10, validation_data = val_set, callbacks=[callbacks])

"""## Evaluasi Model"""

plt.plot(history.history['mae'])
plt.plot(history.history['val_mae'])
plt.title('Akurasi Model')
plt.ylabel('Mae')
plt.xlabel('epoch')
plt.legend(['Train', 'Val'], loc='upper left')
plt.show()

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Loss Model')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['Train', 'Val'], loc='upper left')
plt.show()