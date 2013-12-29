import sys
import os
import csv
import time
import datetime
import Image, ImageDraw

WIDTH=550
MARGIN=5
ROW_HEIGHT=10

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

colors = [
  ("Asked;", (0, 0, 128), "we asked"), # blue
  ("Asked us", (0, 100, 0), "asked us"), # dark green
  ("Asked back", (0, 160, 20), "asked back"), # lighter green
  ("Organized ourselves", (128, 0, 0), "organized ourselves"), # dark red
  ("Applied", (100, 50, 0), "applied"), # yellow
]

def color(how_booked):
  for t, c, _ in colors:
    if t in how_booked:
      return c
  return (128, 128, 128)

def start(in_fname, out_fname):
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

  im.save(out_fname, "PNG")

if __name__ == "__main__":
  start(*sys.argv[1:])
