import os
import pickle
import pydload

import numpy as np

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, TimeDistributed, Activation, dot, concatenate, Bidirectional
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical

def getTextEncodings(texts, parameters):

    encSeq = parameters["enc_token"].texts_to_sequences(texts)
    padSeq = pad_sequences(encSeq, maxlen=parameters["max_encoder_seq_length"],
                            padding='post')
    padSeq = to_categorical(padSeq, num_classes=parameters["enc_vocab_size"])
    return padSeq


def getExtraChars(parameters):
    allowedExtra = []
    for d_c, d_i in parameters["dec_token"].word_index.items():
        if d_c.lower() not in parameters["enc_token"].word_index:
            allowedExtra.append(d_i)
    return allowedExtra

def getModelInstance(parameters):

    encoderInput = Input(shape=(None, parameters["enc_vocab_size"],))
    encoder = Bidirectional(LSTM(128, return_sequences=True, return_state=True),
                            merge_mode='concat')
    encoder_outputs, forward_h, forward_c, backward_h, backward_c = encoder(encoderInput)

    encoderH = concatenate([forward_h, backward_h])
    encoderC = concatenate([forward_c, backward_c])

    decoderInput = Input(shape=(None, parameters["dec_vocab_size"],))
    decoderLstm = LSTM(256, return_sequences=True)
    decoderOutput = decoderLstm(decoderInput, initial_state=[encoderH, encoderC])

    attention = dot([decoderOutput, encoder_outputs], axes=(2, 2))
    attention = Activation('softmax', name='attention')(attention)
    context = dot([attention, encoder_outputs], axes=(2, 1))
    decoderCombined = concatenate([context, decoderOutput])

    output = TimeDistributed(Dense(128, activation="relu"))(decoderCombined)
    output = TimeDistributed(Dense(parameters["dec_vocab_size"], activation="softmax"))(output)

    model = Model([encoderInput, decoderInput], [output])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    return model


def decode(model, parameters, inputText, allowedExtra, batch_size):
    inputTextC = inputText.copy()
    out_dict = {}
    input_sequences = getTextEncodings(inputText, parameters)

    parameters["reverse_dec_dict"][0] = "\n"
    outputs = [""]*len(input_sequences)

    targetText = "\t"
    targetSeq = parameters["dec_token"].texts_to_sequences([targetText]*len(input_sequences))
    targetSeq = pad_sequences(targetSeq, maxlen=parameters["max_decoder_seq_length"],
                               padding="post")
    targetSeqHot = to_categorical(targetSeq, num_classes=parameters["dec_vocab_size"])

    extraCharCount = [0]*len(inputText)
    prevCharIndex = [0]*len(inputText)
    i = 0
    while len(inputText) != 0:
        currCharIndex  = [i - extraCharCount[j] for j in range(len(inputText))]
        input_encodings = np.argmax(input_sequences, axis=2)

        cur_inp_list = [input_encodings[_][currCharIndex[_]] if currCharIndex[_] < len(inputText[_]) else 0 for _ in range(len(inputText))]
        output_tokens = model.predict([input_sequences, targetSeqHot], batch_size=batch_size)
        sampled_possible_indices = np.argsort(output_tokens[:, i, :])[:, ::-1].tolist()
        sampledTokenIndices = []
        for j, per_char_list in enumerate(sampled_possible_indices):
            for index in per_char_list:
                if index in allowedExtra:
                    if parameters["reverse_dec_dict"][index] == '\n' and cur_inp_list[j] != 0:
                        continue
                    elif parameters["reverse_dec_dict"][index] != '\n' and prevCharIndex[j] in allowedExtra:
                        continue
                    sampledTokenIndices.append(index)
                    extraCharCount[j] += 1
                    break
                elif parameters["enc_token"].word_index[parameters["reverse_dec_dict"][index].lower()] == cur_inp_list[j]:
                    sampledTokenIndices.append(index)
                    break

        sampled_chars = [parameters["reverse_dec_dict"][index] for index in sampledTokenIndices]

        outputs = [outputs[j] + sampled_chars[j] for j, output in enumerate(outputs)]
        end_indices = sorted([index for index, char  in enumerate(sampled_chars) if char == '\n'], reverse=True)
        for index in end_indices:
            out_dict[inputText[index]] = outputs[index].strip()
            del  outputs[index]
            del inputText[index]
            del extraCharCount[index]
            del sampledTokenIndices[index]
            input_sequences = np.delete(input_sequences, index, axis=0)
            targetSeq = np.delete(targetSeq, index, axis=0)
        if i == parameters["max_decoder_seq_length"]-1 or len(inputText) == 0:
            break
        targetSeq[:,i+1] = sampledTokenIndices
        targetSeqHot = to_categorical(targetSeq, num_classes=parameters["dec_vocab_size"])
        prevCharIndex = sampledTokenIndices
        i += 1
    outputs = [out_dict[text] for text in inputTextC]
    return outputs


trainedModels = {
            'en': {
                    'checkpoint': 'https://github.com/notAI-tech/fastPunct/releases/download/checkpoint-release/fastpunct_eng_weights.h5',
                    'params': 'https://github.com/notAI-tech/fastPunct/releases/download/checkpoint-release/parameter_dict.pkl'
                },
            
            }

lang_code_mapping = {
    'english': 'en'
}

class Punctuator():
    model = None
    parameters = None
    def __init__(self, lang_code="en", weightsPath=None, params_path=None):
        if lang_code not in trainedModels and lang_code in lang_code_mapping:
            lang_code = lang_code_mapping[lang_code]
        
        home = os.path.expanduser("~")
        langPath = os.path.join(home, '.fastPunct_' + lang_code)
        weightsPath = os.path.join(langPath, 'checkpoint.h5')
        params_path = os.path.join(langPath, 'params.pkl')

        if not os.path.exists(langPath):
            os.mkdir(langPath)

        if not os.path.exists(weightsPath):
            pydload.dload(url=trainedModels[lang_code]['checkpoint'], save_to_path=weightsPath, max_time=None)

        if not os.path.exists(params_path):
            pydload.dload(url=trainedModels[lang_code]['params'], save_to_path=params_path, max_time=None)


        with open(params_path, "rb") as file:
            self.parameters = pickle.load(file)
        self.parameters["reverse_enc_dict"] = {i:c for c, i in self.parameters["enc_token"].word_index.items()}
        self.model = getModelInstance(self.parameters)
        self.model.load_weights(weightsPath)
        self.allowedExtra = getExtraChars(self.parameters)
    
    def punct(self, inputText, batch_size=32):
        inputText = [text.lower() for text in inputText]
        return decode(self.model, self.parameters, inputText, self.allowedExtra, batch_size)

    def fastpunct(self, inputText, batch_size=32):
        return None
    
if __name__ == "__main__":
    print(Punctuator().punct(["Hello my name is Alice today I want to go to the mall" +  
                              "there will be John joining me do you want to join us"]))
