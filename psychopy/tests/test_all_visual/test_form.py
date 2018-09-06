#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import pytest
from psychopy.visual.window import Window
from psychopy.visual.form import Form

class Test_Form(object):
    """Test suite for Form component"""
    def setup_class(self):
        self.questions = []
        self.win = Window(units='height', allowStencil=True)
        # create some questions
        genderItem = {"qText": "What is your gender?",
                      "qWidth": 0.7,
                      "aType": "choice",
                      "aWidth": 0.3,
                      "aOptions": ["Male", "Female", "Other"]}
        self.questions.append(genderItem)
        # then a set of ratings
        items = ["running", "cake", "eating sticks", "programming",
                 "tickling", "being tickled", "cycling", "driving", "swimming"]
        for item in items:
            entry = {"qText": "How much do you like {}".format(item),
                     "qWidth": 0.7,
                     "aType": "rating",
                     "aWidth": 0.3,
                     "aOptions": ["Lots", "Not a lot"]}
            self.questions.append(entry)
        self.survey = Form(self.win, surveyItems=self.questions, size=(1.0, 0.7), pos=(0.0, 0.0))

    def test_respHeight(self):
        for item in self.survey.surveyItems:
            assert self.survey.getRespHeight(item['aOptions']) == (len(item['aOptions']) * self.survey.textHeight)

    def test_questionHeight(self):
        for item in self.survey._items['question']:
            assert self.survey.getQuestionHeight(item) == item.boundingBox[1] / float(self.win.size[1] / 2)

    def test_questionWidth(self):
        for item in self.survey._items['question']:
            assert self.survey.getQuestionWidth(item) == item.boundingBox[0] / float(self.win.size[0] / 2)

    def test_baseYpositions(self):
        survey = Form(self.win, surveyItems=self.questions, size=(1.0, 0.7), pos=(0.0, 0.0))
        positions = [-.075, -.210, -.330, -.450, -.570, -.690, -.810, -.930, -1.050, -1.170]
        for idx, pos in enumerate(survey._baseYpositions):
            assert positions[idx] == round(pos, 3)

    def test_form_size(self):
        assert self.survey.size[0] == (1.0, 0.7)[0]  # width
        assert self.survey.size[1] == (1.0, 0.7)[1]  # height

    def test_apeture_size(self):
        assert self.survey.aperture.size[0] == self.survey.size[0]
        assert self.survey.aperture.size[1] == self.survey.size[1]

    def test_border_limits(self):
        survey = self.survey
        assert survey.leftEdge == survey.pos[0] - survey.size[0]/2.0
        assert survey.rightEdge == survey.pos[0] + survey.size[0]/2.0
        assert survey.topEdge == survey.pos[1] + survey.size[1]/2.0

    def test_text_height(self):
        assert self.survey.textHeight == 0.03

    def test_label_height(self):
        assert self.survey.labelHeight == 0.02

    def test_item_padding(self):
        survey = Form(self.win, surveyItems=self.questions, size=(1.0, 0.7), pos=(0.0, 0.0), itemPadding=0.1)
        assert survey.itemPadding == 0.1

    def test_form_units(self):
        assert self.survey.units == 'height'

    def test_virtual_height(self):
        assert self.survey.virtualHeight == self.survey._baseYpositions[-1] - self.survey.itemPadding

    def test_scroll_offset(self):
        for idx, positions in enumerate([1, 0]):  # 1 is start position
            self.survey.scrollbar.markerPos = positions
            assert round(self.survey._getScrollOffet(), 2) == [0., -.52][idx]

    def test_screen_status(self):
        assert self.survey._inRange(self.survey._items['question'][0])
        with pytest.raises(AssertionError):
            assert self.survey._inRange(self.survey._items['question'][9])

    def teardown_class(self):
        self.win.close()

if __name__ == "__main__":
    test = Test_Form()
    test.setup_class()
    # Add tests
    test.teardown_class()
