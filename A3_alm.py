#!/usr/bin/python
# -*- coding: utf-8 -*-

#    Copyright (C) 2011  Mehmet Atakan Gürkan
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3 as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program (probably in a file named COPYING).
#    If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, print_function

from math import floor, fmod, fabs, atan2, atan, asin, sqrt, sin, cos
import datetime, calendar, ephem, pytz, pyx
from datetime import timedelta as TD
from pyx import path, canvas, color, style, text, graph
from scipy import optimize

from almanac_bg import *
from almanac_utils import *

PI = atan(1)*4.0
mnt_names = ['sıfırıncı', 'Ocak', 'Şubat', 'Mart',
          'Nisan', 'Mayıs', 'Haziran', 'Temmuz',
          'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
mnt_shortnames = ['SFR', 'OCA', 'ŞUB', 'MAR', 'NİS', 'MAY',
               'HAZ', 'TEM', 'AĞU', 'EYL', 'EKİ', 'KAS', 'ARA']

# Local stuff: Here we set the observer's location, timezone and DST
# conventions.
# In addition we set the year for the chart, the limits for the chart,
# and make arrangements for the twilight lines.

obs = ephem.Observer()
# bodrum
#obs.lat  = '37.04'
#obs.long = '27.43'
# ankara
obs.lat  = '39.877'
obs.long = '32.807'
#obsTZ = pytz.timezone('Europe/Istanbul')
obsTZ = pytz.timezone('EET') # Turkey uses Eastern European Time: UTC+2 normal time, +3 summer time
utcTZ = pytz.timezone('UTC')

year = 2012
begin_day_datetime = datetime.datetime(year-1, 12, 31, 12, tzinfo=obsTZ) # noon of the last day of previous year
begin_day = ephem.Date(begin_day_datetime.astimezone(utcTZ)) # convert to UTC
if calendar.isleap(year) :
    no_days = 367
else :
    no_days = 366

for first_sunday in range(1,8) :
    if calendar.weekday(year, 1, first_sunday) == calendar.SUNDAY :
        break
first_sunday_datetime = datetime.datetime(year, 1, first_sunday, 12, tzinfo=obsTZ)

## In Turkey (and in most of Europe), DST rules are:
## Start: Last Sunday in March
## End: Last Sunday in October
## Time: 1.00 am (01:00) Greenwich Mean Time (GMT)
## http://wwp.greenwichmeantime.com/time-zone/rules/eu/index.htm
#for week in range(53) :
#    sunday_datetime = first_sunday_datetime + TD(days=7*week)
#    if (sunday_datetime.month == 3 and
#        (sunday_datetime+TD(days=7)).month == 4) :
#        dst_begin = ephem.Date(sunday_datetime.astimezone(utcTZ))
#    if (sunday_datetime.month == 10 and
#        (sunday_datetime+TD(days=7)).month == 11) :
#        dst_end = ephem.Date(sunday_datetime.astimezone(utcTZ))

class Chart() :
    pass
chart = Chart()
chart.ULcorn = ephem.date(begin_day+4*ephem.hour) # at 4pm (in Ankara Sun does not set earlier than 4pm)
chart.URcorn = ephem.date(chart.ULcorn+16*ephem.hour) # 8 am next day (in Ankara Sun does not rise later than 8am)
chart.LLcorn = ephem.date(chart.ULcorn+no_days)
chart.LRcorn = ephem.date(chart.URcorn+no_days)
chart.width = 22.0
chart.height = 34.0

sun = ephem.Sun()
# Twilights
# In Ankara evening twilight always ends. This would not be true for
# locations much more further than the equator.
eve_twilight = []
mor_twilight = []
obs.horizon = '-18'
for doy in range(no_days) :
    obs.date = begin_day + doy
    eve_twilight.append(obs.next_setting(sun))
    mor_twilight.append(obs.next_rising(sun))
obs.horizon = '0'

# Normal Sunrise and Sunset
sun_rise = []
sun_set = []
for doy in range(no_days) :
    obs.date = begin_day + doy
    sun_set.append(obs.next_setting(sun))
    sun_rise.append(obs.next_rising(sun))

# Objects to be plotted on the chart
class PyEph_body() :
    def __init__(self, pyephem_name, clr=color.cmyk.Gray,
            symbol='~') :
        self.body = pyephem_name
        self.color = clr
        self.symbol = symbol
        self.rising = []
        self.rising_text = []
        self.transit = []
        self.transit_text = []
        self.setting = []
        self.setting_text = []
    def update_rising(self, obs) :
        self.rising.append(obs.next_rising(self.body))
    def update_transit(self, obs) :
        self.transit.append(obs.next_transit(self.body))
    def update_setting(self, obs) :
        self.setting.append(obs.next_setting(self.body))
# planets
mercury = PyEph_body(ephem.Mercury(), color.cmyk.BurntOrange)
venus =   PyEph_body(ephem.Venus(), color.cmyk.CornflowerBlue)
mars =    PyEph_body(ephem.Mars(), color.cmyk.Red)
jupiter = PyEph_body(ephem.Jupiter(), color.cmyk.Magenta)
saturn =  PyEph_body(ephem.Saturn(), color.cmyk.Yellow)
uranus =  PyEph_body(ephem.Uranus(), color.cmyk.SpringGreen)
neptune = PyEph_body(ephem.Neptune(), color.cmyk.ForestGreen)
# some messier objects
m13 = PyEph_body(ephem.readdb("M13,f|C,16:41:42,36:28,5.9,2000,996"))
m31 = PyEph_body(ephem.readdb("M31,f|G,0:42:44,+41:16:8,4.16,2000,11433|3700|35"))
m42 = PyEph_body(ephem.readdb("M42,f|U,05:35:18,-05:23,4,2000,3960"))
m45 = PyEph_body(ephem.readdb("M45,f|U,03:47:0,24:07,1.2,2000,6000"))
# some bright stars
sirius     = PyEph_body(ephem.star('Sirius'))
antares    = PyEph_body(ephem.star('Regulus'))
deneb      = PyEph_body(ephem.star('Deneb'))
betelgeuse = PyEph_body(ephem.star('Betelgeuse'))
pollux     = PyEph_body(ephem.star('Pollux'))

rising_bodies  = [mercury, venus, mars, jupiter, uranus, neptune,
                  m13, m31, m42, m45,
                  sirius, antares, deneb, betelgeuse, pollux]
setting_bodies = [mercury, venus, mars, jupiter, uranus, neptune,
                  m13, m31, m42, m45,
                  sirius, antares, deneb, betelgeuse, pollux]
transit_bodies = [mars, jupiter, uranus, neptune,
                  m13, m31, m42, m45,
                  sirius, antares, deneb, betelgeuse, pollux]

rising_bodies  = [mercury, venus, mars, jupiter, saturn, uranus, neptune]
setting_bodies = [mercury, venus, mars, jupiter, saturn, uranus, neptune]
transit_bodies = [mars, jupiter, saturn, uranus, neptune]


# XXX the +3, -3 bug fix below is a mystery to me,
# XXX but it seems necessary. this probably points out to a deeper
# XXX problem.
for doy in range(no_days+3) :
    obs.date = begin_day + doy -3
    for rb in rising_bodies :
        rb.update_rising(obs)
    for tb in transit_bodies :
        tb.update_transit(obs)
    for sb in setting_bodies :
        sb.update_setting(obs)

pyx.unit.set(defaultunit='cm')
pyx.text.set(mode='latex')
pyx.text.preamble(r'\usepackage[utf8x]{inputenc}')
pyx.text.preamble(r'\usepackage[T1]{fontenc}')
pyx.text.preamble(r'\usepackage{ae,aecompl}')
pyx.text.preamble(r'\usepackage{rotating}')

c = canvas.canvas()

# prepare the limits of the chart and a clippath
ulx, uly = to_chart_coord(sun_set[0], chart)
urx, ury = to_chart_coord(sun_rise[0], chart)
top_line = path.path(path.moveto(ulx, uly),
                     path.lineto(urx, ury))

llx, lly = to_chart_coord(sun_set[-1], chart)
lrx, lry = to_chart_coord(sun_rise[-1], chart)
bot_line = path.path(path.moveto(llx, lly),
                     path.lineto(lrx, lry))

rev_sun_set = sun_set[:]
rev_sun_set.reverse()
clippath = event_to_path(rev_sun_set[:] + sun_rise[:], chart, do_check=False)
clippath.append(path.closepath())

clc = canvas.canvas([canvas.clip(clippath)]) # clipped canvas for paths, text and moon
bclc = canvas.canvas([canvas.clip(clippath)]) # clipped canvas for the background and the dots

# a seperate (larger) clipping canvas for Moon phases
clippath2 = event_to_path([rev_sun_set[0]+2.0] +
        rev_sun_set[:] + [rev_sun_set[-1]-2.0], chart, do_check=False,
            xoffset=-1.3)
clippath2 = clippath2.joined(event_to_path([sun_rise[0]-2.0] +
            sun_rise[:] + [sun_rise[-1]+2.0], chart, do_check=False,
            xoffset=1.3))
clippath2.append(path.closepath())
mclc = canvas.canvas([canvas.clip(clippath2)])

#make_alm_bg(bclc, begin_day_datetime, no_days, chart,
#        obs, sun, sun_set, sun_rise) 
make_alm_bg_vdots(bclc, first_sunday, no_days, chart) 
make_alm_bg_hdots(bclc, first_sunday, no_days, chart) 

# Twilight lines
clc.stroke(event_to_path(eve_twilight, chart),
           [color.cmyk.Gray, style.linewidth.Thin, style.linestyle.dashed])
clc.stroke(event_to_path(mor_twilight, chart),
           [color.cmyk.Gray, style.linewidth.Thin, style.linestyle.dashed])

def add_text_to_path(canv, chart, ev, pos,
        offset=0, sep=1.1, rotate=False, txt1='~', txt2='~',
        txt_color=color.cmyk.Gray) :
    '''Adding text to a given event path.
       ev: event list that forms the path
       pos: a number 0<=x<=1 determining the position of the text along
       the path
       rotate: if True, rotate the text 180 degrees
       txt1: text to go over the path
       txt2: text to go below the path
    '''
    n = len(ev)
    k = int(round(pos*n))
    if k==0 :
        mid = ev[0]
        aft = ev[1]
        x, y = to_chart_coord(mid, chart)
        xa, ya = to_chart_coord(aft, chart)
        slope = atan2(y-ya, x-xa)
    elif k>=n-1 :
        bef = ev[n-2]
        mid = ev[n-1]
        xb, yb = to_chart_coord(bef, chart)
        x, y = to_chart_coord(mid, chart)
        slope = atan2(yb-y, xb-x)
    else :
        bef = ev[k-1]
        mid = ev[k]
        aft = ev[k+1]
        xb, yb = to_chart_coord(bef, chart)
        x, y = to_chart_coord(mid, chart)
        xa, ya = to_chart_coord(aft, chart)
        slope = atan2(yb-ya, xb-xa)
    rot_angle = slope*180.0/PI
    if rotate==True :
        rot_angle += 180.0
#    canv.text(x+offset*sin(slope),
#              y+offset*cos(slope),
#            r'{\small\sffamily %s}' %
#            (txt1),
#            [
#             text.halign.center,text.valign.bottom,
#             pyx.trafo.rotate(rot_angle),
#             color.cmyk.Red])
#    canv.text(x, y,
#              r'{\small\sffamily %s}' % (txt1),
#              [
#               text.halign.center,text.valign.bottom,
#               color.cmyk.Red])
    canv.text(x, y,
              r'\raisebox{%gpt}{\small\sffamily %s}' % (3+offset,txt1),
              [
               text.halign.center,text.valign.bottom,
               pyx.trafo.rotate(rot_angle),
               txt_color])
    canv.text(x, y,
              r'\raisebox{%gpt}{\small\sffamily %s}' % (-6+offset,txt2),
              [
               text.halign.center,text.valign.top,
               pyx.trafo.rotate(rot_angle),
               txt_color])
#    canv.stroke(path.line(x,y,x+2.0*cos(slope),y+2.0*sin(slope)))
#    canv.stroke(path.line(x,y,x-2.0*sin(slope),y+2.0*cos(slope)))

# Moon
moon = ephem.Moon()
moon2 = ephem.Moon()
mooncolorlight = color.rgb(0.6235294,0.6823529,0.827451)
mooncolordark = color.rgb(0.3450980,0.3764706,0.458823)

def S_of_R(R) :
    return (R*R*asin(1.0/R) - 1.0*sqrt(R*R-1.0))/ (PI)

def R_of_S(S) :
    def func(x) :
        return S_of_R(x)-S
    return optimize.bisect(func, 1.0000001, 100.0)

def first_quarter_moon(r, cx, cy) :
    p = path.path(path.moveto(cx, cy))
    p.append(path.arc(cx, cy, r, -90, 90))
    p.append(path.closepath())
    return p
def last_quarter_moon(r, cx, cy) :
    p = path.path(path.moveto(cx, cy))
    p.append(path.arc(cx, cy, r, 90, -90))
    p.append(path.closepath())
    return p

def waxing_moon(X, r, cx, cy) :
    '''draws a waxing moon figure, used for moonset.'''
    p = path.path(path.moveto(cx, cy-r))
    p.append(path.arc(cx, cy, r, -90, 90))
    if X>0.5 :
        R = R_of_S(X-0.5)*r
        theta = asin(r/R)*180/PI
        moon_arc_p = path.arc(cx+sqrt(R*R-r*r), cy, R, 180-theta, 180+theta)
    else :
        R = R_of_S(0.5-X)*r
        theta = asin(r/R)*180/PI
        moon_arc_p = path.arc(cx-sqrt(R*R-r*r), cy, R, -theta, theta)
        p = path.path.reversed(p)
    p.append(moon_arc_p)
    return p

def waning_moon(X, r, cx, cy) :
    '''draws a waning moon figure, used for moonrise.'''
    p = path.path(path.moveto(cx, cy+r))
    p.append(path.arc(cx, cy, r, 90, -90))
    if X>0.5 :
        R = R_of_S(X-0.5)*r
        theta = asin(r/R)*180/PI
        moon_arc_p = path.arc(cx-sqrt(R*R-r*r), cy, R, -theta, theta)
    else :
        R = R_of_S(0.5-X)*r
        theta = asin(r/R)*180/PI
        moon_arc_p = path.arc(cx+sqrt(R*R-r*r), cy, R, 180-theta, 180+theta)
        p = path.path.reversed(p)
    p.append(moon_arc_p)
    return p

for doy in range(no_days) :
    obs.date = begin_day + doy
    mpc = obs.date + 0.5 # moon phase check
    moon_set = obs.next_setting(moon)
    moon2.compute(moon_set)
    X = moon2.moon_phase
    # Waxing moon (moonsets)
    x, y = to_chart_coord(moon_set, chart)
    if (fabs(ephem.next_full_moon(mpc) - mpc) < 0.5 or
        fabs(ephem.previous_full_moon(mpc) - mpc) < 0.5) :
        # full moon
        mclc.stroke(path.circle(x,y,.12),[mooncolorlight,pyx.deco.filled([mooncolorlight])])
    elif ((X < 0.55 and X > 0.45) or 
          fabs(ephem.next_first_quarter_moon(mpc) - mpc) < 0.5 or
          fabs(ephem.previous_first_quarter_moon(mpc) - mpc) < 0.5) :
        # first quarter
        mclc.stroke(first_quarter_moon(0.12, x,y),[mooncolordark,pyx.deco.filled([mooncolordark])])
    elif (fabs(ephem.next_new_moon(mpc) - mpc) < 0.5 or
          fabs(ephem.previous_new_moon(mpc) - mpc) < 0.5):
        # new moon
        mclc.stroke(path.circle(x,y,.12),[mooncolorlight,pyx.deco.filled([mooncolordark])])
    else :
        clc.fill(waxing_moon(X, 0.08, x, y),
                [style.linejoin.bevel,mooncolordark])
    # Waning moon (moonrises)
    moon_rise = obs.next_rising(moon)
    moon2.compute(moon_rise)
    X = moon2.moon_phase
    x, y = to_chart_coord(moon_rise, chart)
    if (fabs(ephem.next_full_moon(mpc) - mpc) < 0.5 or
        fabs(ephem.previous_full_moon(mpc) - mpc) < 0.5) :
        # full moon
        mclc.stroke(path.circle(x,y,.12),[mooncolorlight,pyx.deco.filled([mooncolorlight])])
    elif ((X < 0.55 and X > 0.45) or 
          fabs(ephem.next_last_quarter_moon(mpc) - mpc) < 0.5 or
          fabs(ephem.previous_last_quarter_moon(mpc) - mpc) < 0.5) :
        # last quarter
        mclc.stroke(last_quarter_moon(0.12, x,y),[mooncolorlight,pyx.deco.filled([mooncolorlight])])
    elif (fabs(ephem.next_new_moon(mpc) - mpc) < 0.5 or
          fabs(ephem.previous_new_moon(mpc) - mpc) < 0.5):
        # new moon
        mclc.stroke(path.circle(x,y,.12),[mooncolorlight,pyx.deco.filled([mooncolordark])])
    else :
        clc.fill(waning_moon(X, 0.08, x, y),
                [style.linejoin.bevel,mooncolorlight])

# Planets etc.
mercury.rising_text = [
[0.06, 'Merkür', 'doğuyor', -1, True],
[0.34, 'Merkür', 'doğuyor', -1, False],
[0.595, 'Merkür', 'doğuyor', -1, False],
[0.89, 'Merkür', 'doğuyor', -1, False]
]
venus.rising_text = [
[0.76, 'Venüs doğuyor', '~', -1, True]
]
mars.rising_text = [
[0.12, 'Mars doğuyor', '~', 0, False]
]
jupiter.rising_text = [
[0.62, 'Jüpiter doğuyor', '~', 0, False]
]
saturn.rising_text = [
[0.15, 'Satürn doğuyor', '~', 0, False],
[0.94, 'Satürn doğuyor', '~', 0, False]
]
uranus.rising_text = [
[0.45, 'Uranüs', 'doğuyor', -1, False]
]
neptune.rising_text = [
[0.4, 'Neptün doğuyor', '~', 0, False]
]
for rb in rising_bodies :
    clc.stroke(event_to_path(rb.rising, chart), [rb.color])
    for rstxt in rb.rising_text :
        add_text_to_path(clc, chart, rb.rising, rstxt[0],
                txt1=rstxt[1], txt2=rstxt[2], offset=rstxt[3],
                rotate=rstxt[4], txt_color=rb.color)
mars.transit_text = [
[0.1, 'Mars meridyende', '~', 0, False]
]
jupiter.transit_text = [
[0.06, 'Jüpiter', 'meridyende', -1, False],
[0.87, 'Jüpiter meridyende', '~', 0, False]
]
saturn.transit_text = [
[0.25, 'Satürn meridyende', '~', 0, False]
]
uranus.transit_text = [
[0.014, 'Ur.', 'mrd.', -1, False],
[0.75, 'Uranüs meridyende', '~', 0, False]
]
neptune.transit_text = [
[0.67, '~', 'Neptün meridyende', -1, False]
]
for tb in transit_bodies :
    clc.stroke(event_to_path(tb.transit, chart), [tb.color])
    for tstxt in tb.transit_text :
        add_text_to_path(clc, chart, tb.transit, tstxt[0],
                txt1=tstxt[1], txt2=tstxt[2], offset=tstxt[3],
                rotate=tstxt[4], txt_color=tb.color)
mercury.setting_text = [
[0.16, 'Merkür', 'batıyor', -1, True],
[0.52, 'Merkür', 'batıyor', -1, False],
[0.8, 'Merkür', '~~batıyor', -1, False]
]
venus.setting_text = [
[0.31, 'batıyor', '~', 0, False],
[0.34, 'Venüs ', '~', 0, False]
]
mars.setting_text = [
[0.48, 'Mars batıyor', '~', 0, False]
]
jupiter.setting_text = [
[0.25, 'Jüpiter batıyor', '~', 0, False],
[0.94, 'Jüpiter batıyor', '~', 0, False]
]
saturn.setting_text = [
[0.4, 'Satürn batıyor', '~', 0, False]
]
uranus.setting_text = [
[0.08, '~', 'Uranüs batıyor', -1, False],
[0.94, 'Uranüs batıyor', '~', 0, False]
]
neptune.setting_text = [
[0.07, 'Neptün batıyor', '~', 0, False],
[0.94, 'Neptün batıyor', '~', 0, False]
]
for sb in setting_bodies :
    clc.stroke(event_to_path(sb.setting, chart), [sb.color])
    for sttxt in sb.setting_text :
        add_text_to_path(clc, chart, sb.setting, sttxt[0],
                txt1=sttxt[1], txt2=sttxt[2], offset=sttxt[3],
                rotate=sttxt[4], txt_color=sb.color)


c.insert(bclc)
c.insert(mclc)
c.insert(clc)

# hour labels (from 5pm to 7am)
xincr = chart.width/((chart.URcorn-chart.ULcorn)/ephem.hour)
#for i, tlab in enumerate(['17:00', '18:00', '19:00', '20:00',
#          '21:00', '22:00', '23:00', r'geceyarısı',
#          '01:00', '02:00', '03:00', '04:00',
#          '05:00', '06:00', '07:00']) :
for i, tlab in enumerate(['17', '18', '19', '20',
          '21', '22', '23', r'geceyarısı',
          '01', '02', '03', '04',
          '05', '06', '07']) :
    x = (i+1)*xincr
    y1 = -0.25
    y2 = chart.height+0.15
    c.text(x, y1, tlab, [text.halign.center, text.valign.baseline])
    c.text(x, y2, tlab, [text.halign.center, text.valign.baseline])
x = chart.width*3.0/12.0
y1 = -0.75
y2 = chart.height+0.65
c.text(x, y1, 'AKŞAM', [text.halign.center, text.valign.baseline])
c.text(x, y2, 'AKŞAM', [text.halign.center, text.valign.baseline])
x = chart.width*9.0/12.0
c.text(x, y1, 'SABAH', [text.halign.center, text.valign.baseline])
c.text(x, y2, 'SABAH', [text.halign.center, text.valign.baseline])

## background colouring around the chart to indicate DST
#outDST_col = color.rgb(205.0/255.0, 205.0/255.0, 1.0)
#inDST_col  = color.rgb(241.0/255.0, 215.0/255.0, 241.0/255.0)
#dst_beg_day = int(round(dst_begin-begin_day))
#dst_end_day = int(round(dst_end-begin_day))
#p1 = event_to_path(sun_set[:dst_beg_day], chart, do_check=False)
#p1 = p1.joined(event_to_path(rev_sun_set[-dst_beg_day:],
#            chart, do_check=False, xoffset=-1.4))
#p1.append(path.closepath())
#c.fill(p1, [outDST_col])
#p2 = event_to_path(sun_set[dst_beg_day:dst_end_day], chart, do_check=False)
#p2 = p2.joined(event_to_path(rev_sun_set[-dst_end_day:-dst_beg_day], chart, do_check=False, xoffset=-1.4))
#p2.append(path.closepath())
#c.fill(p2, [inDST_col])
# Days of the month, printed on Sunday evenings and Monday mornings
for sunday in range(first_sunday, no_days, 7) :
    x1 = 0
    x2 = chart.width
    y = chart.height - (sunday * chart.height / no_days)
    mor_date = begin_day_datetime + TD(days=sunday, hours=4)
    mor_x, mor_y = to_chart_coord(sun_set[sunday], chart)
    eve_date = begin_day_datetime + TD(days=sunday, hours=16)
    eve_x, eve_y = to_chart_coord(sun_rise[sunday], chart)
    c.text(mor_x-0.2, y, '%s' % (mor_date.day),
            [text.halign.right, text.valign.middle])
    c.text(eve_x+0.2, y, '%s' % (eve_date.day),
            [text.halign.left, text.valign.middle])
# month labels
for i in range(1,13) :
    dt1_datetime = datetime.datetime(year, i, 14, 12, tzinfo=obsTZ) 
    dt2_datetime = datetime.datetime(year, i, 15, 12, tzinfo=obsTZ) 
    dt3_datetime = datetime.datetime(year, i, 16, 12, tzinfo=obsTZ) 
    n_dt2 = int(dt2_datetime.strftime('%j'))
    x, y = to_chart_coord(sun_set[n_dt2], chart)
    xb, yb = to_chart_coord(sun_set[n_dt2-1], chart)
    xa, ya = to_chart_coord(sun_set[n_dt2+1], chart)
    slope = atan2(ya-yb, xa-xb) 
    c.text(x-1, y,
        r'\begin{turn}{%d}{\Large %s}\end{turn}' %
        (slope*180/PI, mnt_names[i]),
        [text.halign.center, text.valign.middle])
    dt1_datetime = datetime.datetime(year, i, 14, 12, tzinfo=obsTZ) 
    dt2_datetime = datetime.datetime(year, i, 15, 12, tzinfo=obsTZ) 
    dt3_datetime = datetime.datetime(year, i, 16, 12, tzinfo=obsTZ) 
    n_dt2 = int(dt2_datetime.strftime('%j'))
    x, y = to_chart_coord(sun_rise[n_dt2], chart)
    xb, yb = to_chart_coord(sun_rise[n_dt2-1], chart)
    xa, ya = to_chart_coord(sun_rise[n_dt2+1], chart)
    slope = atan2(ya-yb, xa-xb) 
    c.text(x+1, y,
        r'\begin{turn}{%d}{\Large %s}\end{turn}' %
        (slope*180/PI, mnt_names[i]),
        [text.halign.center, text.valign.middle])

c.stroke(top_line)
c.stroke(bot_line)

c.stroke(event_to_path(sun_set, chart))
c.stroke(event_to_path(sun_rise, chart))

c.writePDFfile("almanac_%d_Ankara" % (year))

