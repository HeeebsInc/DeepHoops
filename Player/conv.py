import pickle
import os
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Input, Dropout, Conv1D
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import time
import matplotlib.pyplot as plt
import tensorflow as tf

class LSTMNetwork:
    def __init__(self, player, timestep):
        physical_devices = tf.config.experimental.list_physical_devices('GPU')
        assert len(physical_devices) > 0, "Not enough GPU hardware devices available"
        config = tf.config.experimental.set_memory_growth(physical_devices[0], True)

        t0 = time.time()
        self.player = player
        self.timestep = timestep

        self.player_dir = f'/home/samuel-linux/PycharmProjects/Personal/FantasyBasketball/Data/player-bbref/timestepped/{player}'
        self.pickle_dir = f'{self.player_dir}/pickles'
        self.model_dir = f'{self.player_dir}/models'
        self.model_weights_dir = f'{self.model_dir}/weights'
        self.model_graph_dir = f'{self.model_dir}/graphs'
        self.tts_dict = pickle.load(open(f'{self.pickle_dir}/tts_{self.timestep}.p', 'rb'))

        self.conv_network = self.get_conv()
        t1 = time.time()

        print(f'Total Time to Create and Compile Network: {(t1-t0) // 60}  minutes')



    def get_conv(self):
        x_train_shape = self.tts_dict['x_train'].shape


        model = Sequential()
        model.add(Conv1D(filters = 128, kernel_size = 5, activation='relu', input_shape= (x_train_shape[1], x_train_shape[2]), padding='same'))
        model.add(Dropout(.1))
        model.add(Conv1D(64, kernel_size=5, activation='relu', padding='same'))
        model.add(Dropout(.1))
        model.add(Conv1D(32, kernel_size=5, activation='relu', padding='same'))
        model.add(Dropout(.1))
        model.add(Dense(units=512, activation='relu'))
        model.add(Dense(1))
        model.compile(loss = 'mse', optimizer = 'adam', metrics = ['mse', 'mae'])
        return model



    def train_lstm(self, batch_size, epochs, verbose = 1):
        t0 = time.time()
        x_train, x_test, y_train, y_test = self.tts_dict['x_train'], self.tts_dict['x_test'], self.tts_dict['y_train'], self.tts_dict['y_test']
        print(f'x_train shape: {x_train.shape} | y_train shape: {y_train.shape}')
        print(f'x_test shape: {x_test.shape} | y_test shape: {y_test.shape}')
        early_stopping = EarlyStopping(monitor='val_loss', verbose=1, patience=10, min_delta=.01)
        model_checkpoint = ModelCheckpoint(f'{self.model_weights_dir}/conv_{self.timestep}.h5', verbose=1, save_best_only=True,
                                           monitor='val_loss')
        callbacks = [early_stopping, model_checkpoint]

        history = self.conv_network.fit(x_train, y_train, callbacks= callbacks, validation_data=(x_test, y_test), verbose = verbose,
                                        batch_size= batch_size, epochs = epochs)
        t1 = time.time()
        print(f'Total Time to Train Network {(t1-t0) // 60} minutes | Batch Size = {batch_size} | Epochs = {epochs}')

        self.plot_model_metrics(history, path = f'{self.model_graph_dir}/conv_loss_{self.timestep}.png')

    def plot_model_metrics(self, model_history, path = None):
        train_loss = model_history.history['loss']
        test_loss = model_history.history['val_loss']
        # test_acc = model_history.history['val_acc']
        # train_acc = model_history.history['acc']
        epochs = [i for i in range(1, len(train_loss) + 1)]

        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        ax[0].plot(epochs, train_loss, label='Train Loss')
        ax[0].plot(epochs, test_loss, label='Test Loss')
        ax[0].set_title('Train/Test Loss')
        ax[0].set_xlabel('Epochs')
        ax[0].set_ylabel('Loss (MSE)')
        ax[0].legend()

        if path:
            plt.savefig(path)



if __name__ == '__main__':
    lstm = LSTMNetwork(player = 'Jrue Holiday', timestep= 5)
    lstm.train_lstm(batch_size=2, epochs= 100)