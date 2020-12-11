from typing import Dict, Optional, Tuple

import tensorflow as tf
from tensorflow.keras.layers import GRU, LSTM, Bidirectional, Dense, Dropout, Embedding, SimpleRNN

from .layer import BahdanauAttention

RNN_CELL_MAP: Dict[str, tf.keras.layers.Layer] = {
    "SimpleRNN": SimpleRNN,
    "LSTM": LSTM,
    "GRU": GRU,
}


class RNNSeq2Seq(tf.keras.Model):
    """
    Seq2seq model using RNN cell.

    Arguments:
        cell_type: String, one of (SimpleRNN, LSTM, GRU).
        vocab_size: Integer, the size of vocabulary.
        hidden_dim: Integer, the hidden dimension size of SampleModel.
        num_encoder_layers: Integer, the number of seq2seq encoder.
        num_decoder_layers: Integer, the number of seq2seq decoder.
        dropout: Float dropout rate
        use_bidirectional: Boolean, whether use Bidirectional or not

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
            `[BatchSize, VocabSize]`
    """

    def __init__(
        self,
        cell_type,
        vocab_size,
        hidden_dim,
        num_encoder_layers,
        num_decoder_layers,
        dropout,
        use_bidirectional,
    ):
        super(RNNSeq2Seq, self).__init__()

        assert cell_type in RNN_CELL_MAP, "RNN type is not valid!"

        self.embedding = Embedding(vocab_size, hidden_dim)
        self.dropout = Dropout(dropout)
        self.encoder = [
            # SimpleRNN, LSTM, GRU
            RNN_CELL_MAP[cell_type](
                hidden_dim,
                return_sequences=True,
                return_state=True,
                dropout=dropout,
                recurrent_dropout=dropout,
                name=f"encoder_layer{i}",
            )
            for i in range(num_encoder_layers)
        ]
        self.decoder = [
            # SimpleRNN, LSTM, GRU
            RNN_CELL_MAP[cell_type](
                hidden_dim,
                return_sequences=True,
                return_state=True,
                dropout=dropout,
                recurrent_dropout=dropout,
                name=f"decoder_layer{i}",
            )
            for i in range(num_decoder_layers)
        ]

        if use_bidirectional:
            self.encoder = [Bidirectional(cell, name=f"bi_encoder_layer{i}") for i, cell in enumerate(self.encoder)]
            self.decoder = [Bidirectional(cell, name=f"bi_decoder_layer{i}") for i, cell in enumerate(self.decoder)]
        self.dense = Dense(vocab_size)

    def call(self, inputs: Tuple[tf.Tensor, tf.Tensor], training: Optional[bool] = None):
        encoder_tokens, decoder_tokens = inputs

        # [BatchSize, SequenceLength, HiddenDim]
        encoder_input = self.dropout(self.embedding(encoder_tokens))
        decoder_input = self.dropout(self.embedding(decoder_tokens))

        # [BatchSize, SequenceLength, HiddenDim]
        states = None
        for encoder_layer in self.encoder:
            encoder_input, *states = encoder_layer(encoder_input, initial_state=states)
        for decoder_layer in self.decoder:
            decoder_input, *states = decoder_layer(decoder_input, initial_state=states)

        # [BatchSize, VocabSize]
        output = self.dense(decoder_input[:, -1, :])
        return output


class RNNSeq2SeqWithAttention(tf.keras.Model):
    """
    Seq2seq model using RNN cell with attention.

    Arguments:
        cell_type: String, one of (SimpleRNN, LSTM, GRU).
        vocab_size: Integer, the size of vocabulary.
        hidden_dim: Integer, the hidden dimension size of SampleModel.
        num_encoder_layers: Integer, the number of seq2seq encoder.
        num_decoder_layers: Integer, the number of seq2seq decoder.
        dropout: Float, dropout rate
        use_bidirectional: Boolean, whether use Bidirectional or not

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
            `[BatchSize, VocabSize]`
    """

    def __init__(
        self,
        cell_type,
        vocab_size,
        hidden_dim,
        num_encoder_layers,
        num_decoder_layers,
        dropout,
        use_bidirectional,
    ):
        super(RNNSeq2SeqWithAttention, self).__init__()

        assert cell_type in RNN_CELL_MAP, "RNN type is not valid!"

        self.embedding = Embedding(vocab_size, hidden_dim)
        self.dropout = Dropout(dropout)
        self.encoder = [
            # SimpleRNN, LSTM, GRU
            RNN_CELL_MAP[cell_type](
                hidden_dim,
                return_sequences=True,
                return_state=True,
                dropout=dropout,
                recurrent_dropout=dropout,
                name=f"encoder_layer{i}",
            )
            for i in range(num_encoder_layers)
        ]
        self.decoder = [
            # SimpleRNN, LSTM, GRU
            RNN_CELL_MAP[cell_type](
                hidden_dim,
                return_sequences=True,
                return_state=True,
                dropout=dropout,
                recurrent_dropout=dropout,
                name=f"decoder_layer{i}",
            )
            for i in range(num_decoder_layers)
        ]

        if use_bidirectional:
            self.encoder = [Bidirectional(cell, name=f"bi_encoder_layer{i}") for i, cell in enumerate(self.encoder)]
            self.decoder = [Bidirectional(cell, name=f"bi_decoder_layer{i}") for i, cell in enumerate(self.decoder)]

        self.attention = BahdanauAttention(hidden_dim)
        self.dense = Dense(vocab_size)

    def call(self, inputs: Tuple[tf.Tensor, tf.Tensor], training: Optional[bool] = None):
        encoder_tokens, decoder_tokens = inputs

        # [BatchSize, SequenceLength, HiddenDim]
        encoder_input = self.dropout(self.embedding(encoder_tokens))
        decoder_input = self.dropout(self.embedding(decoder_tokens))

        # [BatchSize, SequenceLength, HiddenDim]
        states = None
        for encoder_layer in self.encoder:
            encoder_input, *states = encoder_layer(encoder_input, initial_state=states)
        context_decoder_input = decoder_input
        for decoder_layer in self.decoder:
            decoder_input, *states = decoder_layer(context_decoder_input, initial_state=states)
            context = self.attention(states[0], encoder_input)
            context_decoder_input = tf.concat([tf.expand_dims(context, axis=1), decoder_input], axis=1)

        # [BatchSize, VocabSize]
        output = self.dense(decoder_input[:, -1, :])
        return output


MODEL_MAP: Dict[str, tf.keras.Model] = {
    "RNNSeq2Seq": RNNSeq2Seq,
    "RNNSeq2SeqWithAttention": RNNSeq2SeqWithAttention,
}
