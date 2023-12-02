import sabre
import os
import sys
os.environ['CUDA_VISIBLE_DEVICES']='-1'
import numpy as np
import tensorflow.compat.v1 as tf
print("TensorFlow version:", tf.__version__)

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import il as network

NN_MODEL = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'model/model')

S_INFO = 6  # bit_rate, buffer_size, next_chunk_size, bandwidth_measurement(throughput and time), chunk_til_video_end
S_LEN = 8  # take how many frames in the past
A_DIM = 6
ACTOR_LR_RATE = 0.0001
BUFFER_NORM_FACTOR = 10.0
# CHUNK_TIL_VIDEO_END_CAP = 48.0
M_IN_K = 1000.0
DEFAULT_QUALITY = 1  # default video quality without agent

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

class ComycoLin(sabre.Abr):
    @property
    def manifest(self):
        return self.session.manifest
    
    @property
    def segments(self):
        return self.manifest.segments

    def __init__(self, strategy):
        self.sess = tf.Session()
        self.actor = network.Network(self.sess,
                                 state_dim=[S_INFO, S_LEN], action_dim=A_DIM,
                                 learning_rate=ACTOR_LR_RATE)
        self.sess.run(tf.global_variables_initializer())
        saver = tf.train.Saver()  
        saver.restore(self.sess, NN_MODEL)
        print("Testing model restored.")
        self.s_batch = [np.zeros((S_INFO, S_LEN))]
        self.bit_rate = DEFAULT_QUALITY
        # # only take first A_DIM Bitrates
        # self.manifest.bitrates = self.manifest.bitrates[:A_DIM]
        # assert len(self.manifest.bitrates) == A_DIM
    
    def get_buffer_size(self):
        buffer_level = self.session.get_buffer_level()
        return buffer_level / 1000
    
    def get_video_chunk_size(self, segment_index):
        video_chunk_size = self.segments[segment_index][self.bit_rate]
        return video_chunk_size

    def get_delay(self, segment_index):
        segment_size = self.segments[segment_index][self.bit_rate]
        # pass bits , returns ms
        delay = self.network.do_download(segment_size) 
        # print("delay: ", delay)
        return delay 

    def get_next_video_chunk_sizes(self, segment_index):
        try:
            next_video_chunk_sizes = self.segments[segment_index + 1][:A_DIM]
            return next_video_chunk_sizes
        except Exception as e:
            return [0,0,0,0,0,0]

    def get_video_chunk_remain(self, segment_index):
        video_chunk_remain = len(self.segments) - (segment_index + 1) 
        return video_chunk_remain
            
    def get_quality_delay(self, segment_index):
        buffer_size = self.get_buffer_size()
        video_chunk_size = self.get_video_chunk_size(segment_index)
        delay = self.get_delay(segment_index)
        next_video_chunk_sizes = self.get_next_video_chunk_sizes(segment_index)
        video_chunk_remain = self.get_video_chunk_remain(segment_index)
        CHUNK_TIL_VIDEO_END_CAP = len(self.segments)

        # retrieve previous state
        if len(self.s_batch) == 0:
            state = [np.zeros((S_INFO, S_LEN))]
        else:
            state = np.array(self.s_batch[-1], copy=True)

        # dequeue history record
        state = np.roll(state, -1, axis=1)

        # predict
        # this should be S_INFO number of terms
        state[0, -1] = self.manifest.bitrates[:A_DIM][self.bit_rate] / float(np.max(self.manifest.bitrates[:A_DIM]))  # last quality
        state[1, -1] = buffer_size / BUFFER_NORM_FACTOR  # 10 sec
        state[2, -1] = float(video_chunk_size) / float(delay) / M_IN_K  # kilo byte / ms
        state[3, -1] = float(delay) / M_IN_K / BUFFER_NORM_FACTOR  # 10 sec
        state[4, :A_DIM] = np.array(next_video_chunk_sizes) / M_IN_K / M_IN_K  # mega byte
        state[5, -1] = np.minimum(video_chunk_remain, CHUNK_TIL_VIDEO_END_CAP) / float(CHUNK_TIL_VIDEO_END_CAP)

        action_prob = self.actor.predict(np.reshape(state, (1, S_INFO, S_LEN)))
        self.bit_rate = np.argmax(action_prob)

        # print("self.bit_rate", self.bit_rate)

        self.s_batch.append(state)

        return (self.bit_rate, 0)
        
        # # default code
        # manifest = self.manifest
        # bitrates = manifest.bitrates
        # throughput = self.session.get_throughput()
        # quality = 0
        # while (quality + 1 < len(bitrates) and
        #     bitrates[quality + 1] <= throughput):
        #     quality += 1

        # print("self.bit_rate", quality)
        # return (quality, 0)
