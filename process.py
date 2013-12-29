import sys
import os
import csv
import time
import datetime
import Image, ImageDraw

WIDTH=550
MARGIN=5
ROW_HEIGHT=10
HIST_HEIGHT=300

# Sorry this is so sloppy and poorly organized.  I'm writing it quickly, and mostly making
# it public only so I can find it again if I'm interested in doing something similar.

def to_epoch(date):
  date = date.replace("\xe2\x80\x91", "-")
  try:
    return float(datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%s"))
  except Exception:
    print date
    raise

def to_image_coord(date_s, min_s, max_s):
  date_p = (date_s - min_s) / (max_s - min_s)  # between 0 and 1
  return (WIDTH - MARGIN - MARGIN - 90) * date_p + MARGIN + 90

def to_hist_coord(date_s, min_s, max_s):
  date_p = (date_s - min_s) / (max_s - min_s)  # between 0 and 1
  return (WIDTH - 10) * date_p + 10

def epoch_at_index(i, max_i, min_confirm_s, max_confirm_s):
  i_p = float(i) / max_i # between 0 and 1
  delta_s = max_confirm_s - min_confirm_s
  return min_confirm_s + (i_p * delta_s)

colors = [
  ("Asked;", (0, 0, 128), "we asked"), # blue
  ("Asked us", (0, 100, 0), "asked us"), # dark green
  ("Asked back", (0, 160, 20), "asked back"), # lighter green
  ("Organized ourselves", (128, 0, 0), "organized ourselves"), # dark red
  ("Applied", (100, 50, 0), "applied"), # yellow
]

histcolors = {
  "asked us": (175,0,0), # dark red
  "we asked": (0,0,220), # blue
}

tour_histcolors = {
  "asked us": (175,0,0), # dark red
  "we asked": (0,0,220), # blue
  "tour asked": (0,220,0), # green
}

def color(how_booked):
  for t, c, _ in colors:
    if t in how_booked:
      return c
  return (128, 128, 128)

def category(how_booked):
  for t, _, c in colors:
    if t in how_booked:
      return c
  return "other"

def start(in_fname, out_fname, hist_fname, tour_hist_fname):
  data = []
  with open(in_fname) as inf:
    for i, row in enumerate(csv.reader(inf)):
      if i == 0:
         continue
      date_confirmed, dance_name, date_played, how_booked = row
      confirmed_s, played_s = to_epoch(date_confirmed), to_epoch(date_played)
      data.append((date_confirmed, confirmed_s,
                   date_played, played_s,
                   dance_name,
                   how_booked))

  min_s, max_s = None, None
  for confirm_d, confirm_s, play_d, play_s, name, how_booked in data:
    if min_s is None or confirm_s < min_s:
      min_s = confirm_s
    if max_s is None or play_s > max_s:
      max_s = play_s

  data.sort()

  offset = 20

  im = Image.new("RGB", (WIDTH, (len(data) * ROW_HEIGHT) + MARGIN + offset), "white")
  draw = ImageDraw.Draw(im)

  # dates along top
  for d in ["2010", "2011", "2012", "2013", "2014", "2015"]:
    x = to_image_coord(to_epoch("%s-01-01" % d), min_s, max_s)
    y = 5
    draw.text((x, y), "| %s" % d, fill=(0,0,0))

  # body of chart
  for i, (confirm_d, confirm_s, play_d, play_s, name, how_booked) in enumerate(data):
    start_x = to_image_coord(confirm_s, min_s, max_s)
    end_x = to_image_coord(play_s, min_s, max_s)
    y = offset + i * ROW_HEIGHT
    draw.line((start_x, y + ROW_HEIGHT/2, end_x, y + ROW_HEIGHT/2), fill=(32,32,32))

    c = color(how_booked)
    if i < 0:
      draw.text((end_x + 10, y), name, fill=c)
    else:
      w, h = draw.textsize(name)
      draw.text((start_x - 10 - w, y), name, fill=c)

  # key
  x = WIDTH-130
  draw.text((x, offset), "key", fill=(0,0,0))
  for i, (_, c, t) in enumerate(colors):
    y = offset + (i+1)*ROW_HEIGHT
    draw.text((x + 10, y), t, fill=c)
  draw.text((x + 10, y + ROW_HEIGHT), "(T) - tour", fill=(0,0,0))
  draw.text((x + 10, y + ROW_HEIGHT*2), "(mT) - mini tour", fill=(0,0,0))

  im.save(out_fname, "PNG")

  # done with main plot, now make histogram plot

  histogram_data = {}
  for cat in histcolors:
    histogram_data[cat] = []

  max_confirm_s = None
  for confirm_d, confirm_s, play_d, play_s, name, how_booked in data:
    if max_confirm_s is None or confirm_s > max_confirm_s:
      max_confirm_s = confirm_s

    cat = category(how_booked)
    if cat == "asked back":
      cat = "asked us"
    elif cat == "applied" or cat == "organized ourselves":
      cat = "we asked"

    if cat != "other":
      histogram_data[cat].append(confirm_s)

  im = Image.new("RGB", (WIDTH, HIST_HEIGHT), "white")
  draw = ImageDraw.Draw(im)

  # dates along top
  for d in ["2010", "2011", "2012", "2013", "2014", "2015"]:
    x = to_image_coord(to_epoch("%s-01-01" % d), min_s, max_s)
    y = 5
    draw.text((x, y), "| %s" % d, fill=(0,0,0))

  # hist body

  draw_points = {} # color -> [coord with unscaled y]

  max_i = WIDTH-20
  for ct in histogram_data:
    fill = histcolors[ct]    

    draw_points[fill] = [(0, 0)] # all lines come from the origin
    for i in range(max_i):
      e = epoch_at_index(i, max_i, min_s, max_confirm_s)
      c = interpolate_value(e, histogram_data[ct])
      draw_points[fill].append((i+1, c))

  max_c = None
  for fill in draw_points:
    for _, c in draw_points[fill]:
      if max_c is None or c > max_c:
        max_c = c

  c_adjust = (HIST_HEIGHT-20)/max_c
  y_offset = HIST_HEIGHT-10

  for fill in draw_points:
    for (i1, c1), (i2, c2) in zip(draw_points[fill], draw_points[fill][1:]):
      x1 = i1 + 10
      x2 = i2 + 10

      y1 = y_offset - (c1 * c_adjust)
      y2 = y_offset - (c2 * c_adjust)

      print x1, y1, x2, y2, fill

      draw.line((x1, y1, x2, y2), fill=fill)

  im.save(hist_fname, "PNG")

  # now make another histogram, this time separating out tour-related requests

  tour_histogram_data = {}
  for cat in tour_histcolors:
    tour_histogram_data[cat] = []

  max_confirm_s = None
  for confirm_d, confirm_s, play_d, play_s, name, how_booked in data:
    if max_confirm_s is None or confirm_s > max_confirm_s:
      max_confirm_s = confirm_s

    cat = category(how_booked)
    if cat == "asked back":
      cat = "asked us"
    elif cat == "applied" or cat == "organized ourselves":
      cat = "we asked"

    if cat == "we asked" and "T)" in name:
      cat = "tour asked"

    if cat != "other":
      tour_histogram_data[cat].append(confirm_s)

  im = Image.new("RGB", (WIDTH, HIST_HEIGHT), "white")
  draw = ImageDraw.Draw(im)

  # dates along top
  for d in ["2010", "2011", "2012", "2013", "2014", "2015"]:
    x = to_image_coord(to_epoch("%s-01-01" % d), min_s, max_s)
    y = 5
    draw.text((x, y), "| %s" % d, fill=(0,0,0))

  # tour hist body

  draw_points = {} # color -> [coord with unscaled y]

  max_i = WIDTH-20
  for ct in tour_histogram_data:
    fill = tour_histcolors[ct]    

    draw_points[fill] = [(0, 0)] # all lines come from the origin
    for i in range(max_i):
      e = epoch_at_index(i, max_i, min_s, max_confirm_s)
      c = interpolate_value(e, tour_histogram_data[ct])
      draw_points[fill].append((i+1, c))

  max_c = None
  for fill in draw_points:
    for _, c in draw_points[fill]:
      if max_c is None or c > max_c:
        max_c = c

  c_adjust = (HIST_HEIGHT-20)/max_c
  y_offset = HIST_HEIGHT-10

  for fill in draw_points:
    for (i1, c1), (i2, c2) in zip(draw_points[fill], draw_points[fill][1:]):
      x1 = i1 + 10
      x2 = i2 + 10

      y1 = y_offset - (c1 * c_adjust)
      y2 = y_offset - (c2 * c_adjust)

      print x1, y1, x2, y2, fill

      draw.line((x1, y1, x2, y2), fill=fill)

  im.save(tour_hist_fname, "PNG")


def interpolate_value(point_at, other_points):
  window = 60*60*24*30*4 # four months

  s = 0
  for other_point in other_points:

    delta_s = abs(point_at - other_point)
    if delta_s > window:
      continue # too far away to include

    consider_p = 1 - (delta_s / window) # between 0 and 1

    s += consider_p # linear kernel

  return s

if __name__ == "__main__":
  start(*sys.argv[1:])
