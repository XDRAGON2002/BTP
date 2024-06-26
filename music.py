# -*- coding: utf-8 -*-
"""music.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1IxUvV4FYctvOwfJyym1wArL5v9PfmMyG

# Importing Libraries

We use a plethora of libraries for our task at hand ranging from libraries for data preprocessing, transformation, visualization, analysis, modelling and especially for interpreting and working with musical data
"""

from google.colab import drive

drive.mount("/content/gdrive")

import glob
from music21 import converter, instrument, note, chord, stream
import numpy as np
import tensorflow as tf
from tensorflow import keras
import pickle
import nltk
import random
import math
import collections
import matplotlib.pyplot as plt
import seaborn as sns
import librosa

"""# Preprocessing

The dataset we are using is from a game called Final Fantasy VII and we are using the piano instrument sounds to be able to generate new piano instrument sounds.

We are using the .midi file format as it presents us with an easy interface for extracting all the nodes and chords present in each sound file.

So we extract all the piano notes and chords from all files and store them together in a notes list sequence. To save time we also store these notes in a pickle object file for easy access in subsequent runs.

We also go ahead and define various utility functions such as applying laplace smoothing for probabilistic models, perplexity for probabilistic models as a metric for comparision between different models.

Moreover, since we are using a music based data set, we also need to define some new metrics which take the context as music instead of completely treating it as a natural language.

So, we use a time vs pitch graph to figure out how the generated notes vary over a period of time to ensure there is no observant continuity breaks or inconsistency to break the melody.

We also use comparision between the generated chord sequences and the chord sequences that originally existed in the data to see how many patterns the model is able to learn and adapt to.
"""

notes = []

for file in glob.glob("gdrive/MyDrive/Music Gen/data/*.mid"):
    midi = converter.parse(file)
    notes_to_parse = None

    parts = instrument.partitionByInstrument(midi)

    if parts:
        notes_to_parse = parts.parts[0].recurse()
    else:
        notes_to_parse = midi.flat.notes

    for element in notes_to_parse:
        if isinstance(element, note.Note):
            notes.append(str(element.pitch))
        elif isinstance(element, chord.Chord):
            notes.append(".".join(str(n) for n in element.normalOrder))

with open ("gdrive/MyDrive/Music Gen/artifacts/notes", "rb") as fp:
    notes = pickle.load(fp)

n_vocab = len(set(notes))

def laplace_smooth(n_gram, n_count, n_gram_prev, n_gram_prev_count):
    m_count = n_gram_prev_count[n_gram_prev]
    return (n_count + 1) / (m_count + 1 * n_vocab)

def perplexity(notes, grams, n_gram_model):
    n_grams = nltk.ngrams(notes, grams)
    probabilities = [n_gram_model[n_gram] for n_gram in n_grams]
    return math.exp((-1/len(notes)) * sum(map(math.log, probabilities)))

def plot_pitch_time(audio_file):
    y, sr = librosa.load(audio_file)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    pitch_mean = pitches.mean(axis=0)
    time = np.arange(len(pitch_mean)) * librosa.frames_to_time(1, sr=sr)
    plt.figure(figsize=(12, 6))
    plt.plot(time, pitch_mean, label='Pitch (Hz)')
    plt.xlabel('Time (s)')
    plt.ylabel('Pitch (Hz)')
    plt.title('Pitch vs. Time')
    plt.legend()
    plt.show()

def get_common_chord_progressions(prediction_output):
    output_chords = list(filter(lambda x: '.' in x, prediction_output))
    output_three_chord_progressions = nltk.ngrams(output_chords, 3)
    output_three_chord_progressions_count = nltk.FreqDist(output_three_chord_progressions)

    print(f"Unique three chord progressions: {len(output_three_chord_progressions_count)}")

    output_four_chord_progressions = nltk.ngrams(output_chords, 4)
    output_four_chord_progressions_count = nltk.FreqDist(output_four_chord_progressions)

    print(f"Unique four chord progressions: {len(output_four_chord_progressions_count)}")
    print()

    for progression, count in output_three_chord_progressions_count.items():
        if progression in dict(three_chord_progressions_count):
            print(progression, count, dict(three_chord_progressions_count)[progression])
    print()
    for progression, count in output_four_chord_progressions_count.items():
        if progression in dict(four_chord_progressions_count):
            print(progression, count, dict(four_chord_progressions_count)[progression])

print(n_vocab)

"""# EDA

We analyze and find what all notes and chords are present in the dataset as well as what the most frequently appearing ones are.

Along with finding out the chord sequences in the orignal dataset, we are only considering 3 length or 4 length sequences are they are the most important ones in a majority of melodies.
"""

len(notes), notes[0], notes[1], len(set(notes))

notes_freq = dict(sorted(dict(collections.Counter(notes)).items(), key=lambda x: (x[1], x[0]), reverse=True)[:20])
plt.xticks(rotation = 90)
plt.bar(notes_freq.keys(), [4000 * x for x in notes_freq.values()])

tempn = list(filter(lambda x: '.' not in x, list((notes))))
tempn_freq = dict(sorted(dict(collections.Counter(tempn)).items(), key=lambda x: (x[1], x[0]), reverse=True)[:20])
plt.xticks(rotation = 90)
plt.bar(tempn_freq.keys(), [4000 * x for x in tempn_freq.values()])

tempc = list(filter(lambda x: '.' in x, list((notes))))
tempc_freq = dict(sorted(dict(collections.Counter(tempc)).items(), key=lambda x: (x[1], x[0]), reverse=True)[:20])
plt.xticks(rotation = 90)
plt.bar(tempc_freq.keys(), [4000 * x for x in tempc_freq.values()])

tempc2 = list(filter(lambda x: len(x.split('.')) > 2, list((notes))))
tempc2_freq = dict(sorted(dict(collections.Counter(tempc2)).items(), key=lambda x: (x[1], x[0]), reverse=True)[:20])
plt.xticks(rotation = 90)
plt.bar(tempc2_freq.keys(), [4000 * x for x in tempc2_freq.values()])

len(tempc)

len(tempn) * 4000, len(tempc) * 4000

plt.pie([178548183, 50166621], labels=["Notes", "Chords"])
plt.legend()
plt.show()

three_chord_progressions = nltk.ngrams(tempc, 3)
three_chord_progressions_count = nltk.FreqDist(three_chord_progressions)

three_chord_progressions_count

four_chord_progressions = nltk.ngrams(tempc, 4)
four_chord_progressions_count = nltk.FreqDist(four_chord_progressions)

four_chord_progressions_count

"""# Bigram

The bigram results are not that impressive since the next note depends completely on the previous one, so given that repetitions exist in music, it gets stuck in a loop of generating the same infinite sequence and hence doesn't has a good frequency-time graph, neither learns any chord sequences but has good perplexity since it has less choices.
"""

bigrams = nltk.ngrams(notes, 2)
bigrams_count = nltk.FreqDist(bigrams)

bigrams_prev = nltk.ngrams(notes, 1)
bigrams_prev_count = nltk.FreqDist(bigrams_prev)

bigram_model = {bigram: laplace_smooth(bigram, bigram_count, bigram[:-1], bigrams_prev_count) for bigram, bigram_count in bigrams_count.items()}

start = random.choice(list(dict(bigrams_prev_count.items()).keys()))

pattern = [*start]
prediction_output = []

for note_index in range(500):
    candidates = [[bigram[-1], prob] for bigram, prob in bigram_model.items() if list(bigram[:-1]) == pattern]
    candidates = sorted(candidates, key=lambda candidate: candidate[1], reverse=True)
    if len(candidates) == 0:
        start = random.choice(list(dict(bigrams_prev_count.items()).keys()))
        pattern = [*start]
        result = pattern[-1]
    else:
        result = candidates[0][0]
    prediction_output.append(result)
    pattern.append(result)
    pattern = pattern[1:]

offset = 0
output_notes = []

for pattern in prediction_output:
    if ("." in pattern) or (pattern.isdigit()):
        notes_in_chord = pattern.split('.')
        new_notes = []
        for current_note in notes_in_chord:
            new_note = note.Note(int(current_note))
            new_note.storedInstrument = instrument.Piano()
            new_notes.append(new_note)
        new_chord = chord.Chord(new_notes)
        new_chord.offset = offset
    else:
        new_note = note.Note(pattern)
        new_note.offset = offset
        new_note.storedInstrument = instrument.Piano()
        output_notes.append(new_note)
    offset += 0.5

midi_stream = stream.Stream(output_notes)
midi_stream.write("midi", fp="gdrive/MyDrive/Music Gen/test_output_bigram.mid")

perplexity(notes, 2, dict(bigrams_count.items()))

plot_pitch_time("gdrive/MyDrive/Music Gen/test_output_bigram.wav")

get_common_chord_progressions(prediction_output)

"""# Trigram

Improvement over the bigram, but still gets stuck with the same problem of infinite sequence generation, slightly better graph and chord sequences, worse perplexity since choices increase.
"""

trigrams = nltk.ngrams(notes, 3)
trigrams_count = nltk.FreqDist(trigrams)

trigrams_prev = nltk.ngrams(notes, 2)
trigrams_prev_count = nltk.FreqDist(trigrams_prev)

trigram_model = {trigram: laplace_smooth(trigram, trigram_count, trigram[:-1], trigrams_prev_count) for trigram, trigram_count in trigrams_count.items()}

start = random.choice(list(dict(trigrams_prev_count.items()).keys()))

pattern = [*start]
prediction_output = []

for note_index in range(500):
    candidates = [[trigram[-1], prob] for trigram, prob in trigram_model.items() if list(trigram[:-1]) == pattern]
    candidates = sorted(candidates, key=lambda candidate: candidate[1], reverse=True)
    if len(candidates) == 0:
        start = random.choice(list(dict(trigrams_prev_count.items()).keys()))
        pattern = [*start]
        result = pattern[-1]
    else:
        result = candidates[0][0]
    prediction_output.append(result)
    pattern.append(result)
    pattern = pattern[1:]

offset = 0
output_notes = []

for pattern in prediction_output:
    if ("." in pattern) or (pattern.isdigit()):
        notes_in_chord = pattern.split('.')
        new_notes = []
        for current_note in notes_in_chord:
            new_note = note.Note(int(current_note))
            new_note.storedInstrument = instrument.Piano()
            new_notes.append(new_note)
        new_chord = chord.Chord(new_notes)
        new_chord.offset = offset
    else:
        new_note = note.Note(pattern)
        new_note.offset = offset
        new_note.storedInstrument = instrument.Piano()
        output_notes.append(new_note)
    offset += 0.5

midi_stream = stream.Stream(output_notes)
midi_stream.write("midi", fp="gdrive/MyDrive/Music Gen/test_output_trigram.mid")

perplexity(notes, 3, dict(trigrams_count.items()))

plot_pitch_time("gdrive/MyDrive/Music Gen/test_output_trigram.wav")

get_common_chord_progressions(prediction_output)

"""# Fiftygram

Much better performing than bigram and trigram, improved graph and chord sequence matches, worse perplexity again because of increase in choices.
"""

fiftygrams = nltk.ngrams(notes, 50)
fiftygrams_count = nltk.FreqDist(fiftygrams)

fiftygrams_prev = nltk.ngrams(notes, 49)
fiftygrams_prev_count = nltk.FreqDist(fiftygrams_prev)

fiftygram_model = {fiftygram: laplace_smooth(fiftygram, fiftygram_count, fiftygram[:-1], fiftygrams_prev_count) for fiftygram, fiftygram_count in fiftygrams_count.items()}

start = random.choice(list(dict(fiftygrams_prev_count.items()).keys()))

pattern = [*start]
prediction_output = []

for note_index in range(500):
    candidates = [[fiftygram[-1], prob] for fiftygram, prob in fiftygram_model.items() if list(fiftygram[:-1]) == pattern]
    candidates = sorted(candidates, key=lambda candidate: candidate[1], reverse=True)
    if len(candidates) == 0:
        start = random.choice(list(dict(fiftygrams_prev_count.items()).keys()))
        pattern = [*start]
        result = pattern[-1]
    else:
        result = candidates[0][0]
    prediction_output.append(result)
    pattern.append(result)
    pattern = pattern[1:]

offset = 0
output_notes = []

for pattern in prediction_output:
    if ("." in pattern) or (pattern.isdigit()):
        notes_in_chord = pattern.split('.')
        new_notes = []
        for current_note in notes_in_chord:
            new_note = note.Note(int(current_note))
            new_note.storedInstrument = instrument.Piano()
            new_notes.append(new_note)
        new_chord = chord.Chord(new_notes)
        new_chord.offset = offset
    else:
        new_note = note.Note(pattern)
        new_note.offset = offset
        new_note.storedInstrument = instrument.Piano()
        output_notes.append(new_note)
    offset += 0.5

midi_stream = stream.Stream(output_notes)
midi_stream.write("midi", fp="gdrive/MyDrive/Music Gen/test_output_fiftygram.mid")

perplexity(notes, 50, dict(fiftygrams_count.items()))

plot_pitch_time("gdrive/MyDrive/Music Gen/test_output_fiftygram.wav")

get_common_chord_progressions(prediction_output)

"""# Hundredgram

Best probabilistic n-gram model so far, much better graph and chord sequences, again worse perplexity due to choices increasing many fold.
"""

hundredgrams = nltk.ngrams(notes, 100)
hundredgrams_count = nltk.FreqDist(hundredgrams)

hundredgrams_prev = nltk.ngrams(notes, 99)
hundredgrams_prev_count = nltk.FreqDist(hundredgrams_prev)

hundredgram_model = {hundredgram: laplace_smooth(hundredgram, hundredgram_count, hundredgram[:-1], hundredgrams_prev_count) for hundredgram, hundredgram_count in hundredgrams_count.items()}

start = random.choice(list(dict(hundredgrams_prev_count.items()).keys()))

pattern = [*start]
prediction_output = []

for note_index in range(500):
    candidates = [[hundredgram[-1], prob] for hundredgram, prob in hundredgram_model.items() if list(hundredgram[:-1]) == pattern]
    candidates = sorted(candidates, key=lambda candidate: candidate[1], reverse=True)
    if len(candidates) == 0:
        start = random.choice(list(dict(hundredgrams_prev_count.items()).keys()))
        pattern = [*start]
        result = pattern[-1]
    else:
        result = candidates[0][0]
    prediction_output.append(result)
    pattern.append(result)
    pattern = pattern[1:]

prediction_output

offset = 0
output_notes = []

for pattern in prediction_output:
    if ("." in pattern) or (pattern.isdigit()):
        notes_in_chord = pattern.split('.')
        new_notes = []
        for current_note in notes_in_chord:
            new_note = note.Note(int(current_note))
            new_note.storedInstrument = instrument.Piano()
            new_notes.append(new_note)
        new_chord = chord.Chord(new_notes)
        new_chord.offset = offset
    else:
        new_note = note.Note(pattern)
        new_note.offset = offset
        new_note.storedInstrument = instrument.Piano()
        output_notes.append(new_note)
    offset += 0.5

midi_stream = stream.Stream(output_notes)
midi_stream.write("midi", fp="gdrive/MyDrive/Music Gen/test_output_hundredgram.mid")

perplexity(notes, 100, dict(hundredgrams_count.items()))

plot_pitch_time("gdrive/MyDrive/Music Gen/test_output_hundredgram.wav")

get_common_chord_progressions(prediction_output)

"""# LSTM

Using an LSTM based approach we get a model, that has stable graph along with almost identical chord sequences which is great.
"""

sequence_length = 100

pitchnames = sorted(set(item for item in notes))

n_vocab = len(set(notes))

note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

network_input_data = []
network_output = []

for i in range(0, len(notes) - sequence_length, 1):
    sequence_in = notes[i:i + sequence_length]
    sequence_out = notes[i + sequence_length]

    network_input_data.append([note_to_int[char] for char in sequence_in])
    network_output.append(note_to_int[sequence_out])

n_patterns = len(network_input_data)

network_input = np.reshape(network_input_data, (n_patterns, sequence_length, 1))
network_input = network_input / float(n_vocab)

network_output = keras.utils.to_categorical(network_output)

music_model = keras.Sequential([
    # keras.layers.LSTM(512, input_shape=(network_input.shape[1], network_input.shape[2]), return_sequences=True),
    keras.layers.LSTM(512, input_shape=(100, 100), return_sequences=True),
    keras.layers.Dropout(0.3),
    keras.layers.LSTM(512, return_sequences=True),
    keras.layers.Dropout(0.3),
    keras.layers.LSTM(512),
    keras.layers.Dense(256, activation="relu"),
    keras.layers.Dropout(0.3),
    # keras.layers.Dense(n_vocab, activation="softmax"),
    keras.layers.Dense(1408732, activation="softmax"),
])

music_model.summary()

tf.keras.utils.plot_model(music_model, show_shapes=True, show_dtype=True, show_layer_activations=True)

model.compile(optimizer="rmsprop", loss="categorical_crossentropy", metrics=["accuracy"])

hist = model.fit(network_input, network_output, epochs=200, batch_size=64)

model.load_weights("gdrive/MyDrive/Music Gen/weights.hdf5")

start = np.random.randint(0, len(network_input) - 1)

int_to_note = dict((number, note) for number, note in enumerate(pitchnames))

pattern = network_input_data[start]
prediction_output = []

for note_index in range(500):
    prediction_input = np.reshape(pattern, (1, len(pattern), 1))
    prediction_input = prediction_input / float(n_vocab)

    prediction = model.predict(prediction_input, verbose=0)

    index = np.argmax(prediction)
    result = int_to_note[index]
    prediction_output.append(result)

    pattern.append(index)
    pattern = pattern[1:len(pattern)]

offset = 0
output_notes = []

for pattern in prediction_output:
    if ("." in pattern) or (pattern.isdigit()):
        notes_in_chord = pattern.split('.')
        new_notes = []
        for current_note in notes_in_chord:
            new_note = note.Note(int(current_note))
            new_note.storedInstrument = instrument.Piano()
            new_notes.append(new_note)
        new_chord = chord.Chord(new_notes)
        new_chord.offset = offset
    else:
        new_note = note.Note(pattern)
        new_note.offset = offset
        new_note.storedInstrument = instrument.Piano()
        output_notes.append(new_note)
    offset += 0.5

midi_stream = stream.Stream(output_notes)
midi_stream.write("midi", fp="gdrive/MyDrive/Music Gen/test_output_lstm.mid")

plot_pitch_time("gdrive/MyDrive/Music Gen/test_output_lstm.wav")

get_common_chord_progressions(prediction_output)