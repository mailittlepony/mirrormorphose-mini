#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import numpy as np
import logging

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite.python.interpreter import Interpreter

logger = logging.getLogger(__name__)


class GazeModel:
    def __init__(self, model_path, input_shape, class_labels):
        self._interpreter = Interpreter(model_path=model_path)
        self._interpreter.allocate_tensors()

        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()
        self._input_shape = input_shape
        self._class_labels = class_labels

        logger.info("Gaze model initialized.")

    def predict(self, image):
        input_tensor = np.expand_dims(image.astype(np.float32) / 255.0, axis=0)
        self._interpreter.set_tensor(self._input_details[0]['index'], input_tensor)
        self._interpreter.invoke()
        output = self._interpreter.get_tensor(self._output_details[0]['index'])
        return self._class_labels[np.argmax(output[0])]
