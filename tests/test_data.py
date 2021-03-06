import os

import pytest
import tensorflow as tf

from seq2seq.data import get_dataset, get_tfrecord_dataset, make_train_examples


class PseudoTokenizer:
    def tokenize(self, text):
        return tf.strings.unicode_decode("2" + text + "3", "UTF-8")


@pytest.fixture(scope="session")
def data_path():
    return os.path.join((os.path.dirname(__file__)), "data")


def test_get_dataset(data_path):
    dataset = get_dataset(os.path.join(data_path, "sample_dataset.txt"), PseudoTokenizer(), False).map(
        make_train_examples
    )

    data = next(iter(dataset))
    (encoder_input, decoder_input), labels = data
    tf.debugging.assert_equal(tf.shape(encoder_input), [14, 7])
    tf.debugging.assert_equal(tf.shape(decoder_input), [14, 15])
    tf.debugging.assert_equal(tf.shape(labels), [14])

    batch_data = next(iter(dataset.flat_map(lambda x, y: tf.data.Dataset.from_tensor_slices((x, y))).padded_batch(20)))
    (encoder_input, decoder_input), labels = batch_data
    tf.debugging.assert_equal(tf.shape(encoder_input), [20, 13])
    tf.debugging.assert_equal(tf.shape(decoder_input), [20, 15])
    tf.debugging.assert_equal(tf.shape(labels), [20])


def test_get_tfrecord_dataset(data_path):
    tfrecord_dataset = get_tfrecord_dataset(os.path.join(data_path, "sample_dataset.tfrecord")).map(make_train_examples)
    assert len(list(tfrecord_dataset)) == 8

    data = next(iter(tfrecord_dataset))
    (encoder_input, decoder_input), labels = data
    tf.debugging.assert_equal(tf.shape(encoder_input), [12, 13])
    tf.debugging.assert_equal(tf.shape(decoder_input), [12, 13])
    tf.debugging.assert_equal(tf.shape(labels), [12])
