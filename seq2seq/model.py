from typing import Optional, Tuple

import tensorflow as tf


class RNNSeq2Seq(tf.keras.Model):
    """
    Seq2seq model using RNN cell.

    Arguments:
        vocab_size: Integer, the size of vocabulary.
        hidden_dim: Integer, the hidden dimension size of SampleModel.
        cell_type: String, one of (SimpleRNN, LSTM, GRU).

    Call arguments:
        inputs: A tuple (encoder_tokens, decoder_tokens)
            encoder_tokens: A 3D tensor, with shape of `[BatchSize, EncoderSequenceLength]`.
                                all values are in [0, VocabSize).
            decoder_tokens: A 3D tensor, with shape of `[BatchSize, DecoderSequenceLength]`.
                                all values are in [0, VocabSize).
        training: Python boolean indicating whether the layer should behave in
            training mode or in inference mode. Only relevant when `dropout` or
            `recurrent_dropout` is used.

    Output Shape:
        2D tensor with shape:
            `[BatchSize, VocabSize]
    """

    def __init__(self, vocab_size, hidden_dim, cell_type):
        super(RNNSeq2Seq, self).__init__()

        assert cell_type in ("SimpleRNN", "LSTM", "GRU"), "RNN type is not valid!"

        self.embedding = tf.keras.layers.Embedding(vocab_size, hidden_dim)
        self.encoder = tf.keras.layers.Bidirectional(getattr(tf.keras.layers, cell_type)(hidden_dim, return_state=True))
        self.decoder = tf.keras.layers.Bidirectional(getattr(tf.keras.layers, cell_type)(hidden_dim))
        self.dense = tf.keras.layers.Dense(vocab_size)

    def call(self, inputs: Tuple[tf.Tensor, tf.Tensor], training: Optional[bool] = None):
        encoder_tokens, decoder_tokens = inputs

        # [BatchSize, SequenceLength, VocabSize]
        encoder_embedding = self.embedding(encoder_tokens)
        decoder_embedding = self.embedding(decoder_tokens)

        # [BatchSize, SequenceLength, HiddenDim]
        encoded, *encoder_states = self.encoder(encoder_embedding)
        decoded = self.decoder(decoder_embedding, initial_state=encoder_states)

        # [BatchSize, VocabSize]
        output = self.dense(decoded)
        return output
