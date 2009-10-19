## -*- coding: utf-8 -*-

"""
Copyright 2009 Hiroshi Ichikawa (Gimite)
 
Licensed under GPL 2.
"""

import logging
import re
import time
import urllib
import uromkan
from waveapi import events
from waveapi import model
from waveapi import robot
from waveapi import document
from google.appengine.api import urlfetch

def OnRobotAdded(properties, context):
  root_wavelet = context.GetRootWavelet()
  root_wavelet.CreateBlip().GetDocument().SetText(
      u'ローマ字を[]でくくって入力すると、日本語に変換されます。' +
      u'[Hローマ字]でひらがな、[Kローマ字]でカタカナが出ます。' +
      u'Social IME APIを使っています。')

def OnBlipSubmitted(properties, context):
  None

def OnDocumentChanged(properties, context):
  doc = context.GetBlipById(properties['blipId']).GetDocument()
  input = doc.GetText()
  delta = 0
  for m in re.finditer(ur'\[([\u0020-\u007e]+?)\]', input):
    
    roman = re.sub(ur'\s+', u'', m.group(1))
    m2 = re.search(ur'^([HK])(.+)$', roman)
    if m2:
      script = m2.group(1)
      roman = m2.group(2)
    else:
      script = None
    roman = re.sub(ur'(c+)([aiueoy])',
        lambda m: 'k' * len(m.group(1)) + m.group(2), roman)
    hira = re.sub(r"'", '', uromkan.romkan(roman.encode('utf-8')))
    
    if script == u'H':
      output = unicode(hira, 'utf-8')
    elif script == u'K':
      output = unicode(uromkan.hirakata(hira), 'utf-8')
    else:
      url = 'http://www.social-ime.com/api/?string=%s&charset=utf-8' % urllib.quote(hira)
      logging.debug(url)
      res = urlfetch.fetch(url, deadline=10)
      content = unicode(res.content, 'utf-8')
      output = u''
      for line in content.split(u'\n')[:-1]:
        output += line.split(u'\t')[0]
    
    # Inserts and then deletes, instead of using SetTextInRange, to prevent caret
    # to move before the inserted string.
    doc.InsertText(m.start(0) + delta, output)
    delta += len(output)
    doc.DeleteRange(
        document.Range(m.start(0) + delta, m.end(0) + delta))
    delta -= len(m.group(0))

if __name__ == '__main__':
  app_name = 'kanjy-wave'
  my_robot = robot.Robot(app_name, 
      image_url='http://%s.appspot.com/images/icon.png' % app_name,
      # Forces reloading every time, useful for debugging.
      version=str(int(time.time())),
      profile_url='http://%s.appspot.com/' % app_name)
  my_robot.RegisterHandler(events.WAVELET_SELF_ADDED, OnRobotAdded)
  my_robot.RegisterHandler(events.BLIP_SUBMITTED, OnBlipSubmitted)
  my_robot.RegisterHandler(events.DOCUMENT_CHANGED, OnDocumentChanged)
  my_robot.Run()

