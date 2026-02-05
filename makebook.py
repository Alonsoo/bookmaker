#!/usr/bin/env python3

from pypdf import PdfReader, PdfWriter, PageObject, Transformation
import shutil, os, sys
import math
import argparse

parser = argparse.ArgumentParser(description="Simple script to reorder and join pages from a pdf file for printing in booklets.")

parser.add_argument("path", type=str, help="The path of the source pdf file")
parser.add_argument("-s", "--section-size", type=int, default=0, help="Number of sheets per section (each sheet will contain 4 pages from the pdf). If this argument is not present the script will skip reordering the pdf.")
parser.add_argument("-p", "--padding", type=int, default=2, help="Number of blank pages to add at the start of the pdf. Default is 2. This only happens if --section-size argument is present.")
parser.add_argument("-j", "--join", action="store_true", help="If present the script will join pairs of pages into a single landscape oriented page double the width of the original pdf.")

args = parser.parse_args()

if args.section_size <= 0 and not args.join:
    print("No flags given. Nothing happened. See 'makebook -h' for usage.")
    sys.exit(1)

path = args.path
output_path = path[:-4] + "_book.pdf"
TEMP_PATH = "temp.pdf"

section_size = args.section_size
start_padding = args.padding

shutil.copy(path, TEMP_PATH)


###   PAD AND REORDER PDF INTO BOOKLETS   ###
if section_size > 0:
    reader = PdfReader(TEMP_PATH)

    start_padding = 2

    num_pages = len(reader.pages) + start_padding
    num_sections = math.ceil(num_pages / (section_size*4))
    end_padding = (num_sections * section_size * 4) - num_pages

    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    for _ in range(start_padding):
        writer.insert_blank_page(index=0)

    for _ in range(end_padding):
        writer.add_blank_page()


    with open(TEMP_PATH, "wb") as f:
        writer.write(f)

    reader = PdfReader(TEMP_PATH)
    writer = PdfWriter()


    order = []
    for i in range(section_size):
        offset = i*2
        order.append(section_size*4 - 1 - offset)
        order.append(0 + offset)
        order.append(1 + offset)
        order.append(section_size*4 - 2 - offset)


    for i in range(len(reader.pages)):
        current_section = i // (section_size * 4)
        page_in_section = i % (section_size * 4)
        index = current_section * section_size * 4 + order[page_in_section]
        writer.add_page(reader.pages[index])



    with open(TEMP_PATH, "wb") as f:
        writer.write(f)


    print(f"Reordered document into sections of {section_size} sheets ({section_size*4} pages) each for a total of {num_sections} sections ({num_sections*section_size*4} pages)")
    print(f"    Added {start_padding} blank pages at the start and {end_padding} at the end")




###   JOIN PAGES INTO LANDSCAPE PAIRS   ###

if args.join:
    reader = PdfReader(TEMP_PATH)
    writer = PdfWriter()

    width = reader.pages[0].mediabox.width
    height = reader.pages[0].mediabox.height

    new_width = width * 2

    for i in range(0, len(reader.pages), 2):
        new_page = PageObject.create_blank_page(width=new_width, height=height)
        new_page.merge_page(reader.pages[i])
        new_page.merge_transformed_page(
            reader.pages[i+1],
            Transformation().translate(tx=width, ty=0)
        )

        writer.add_page(new_page)

    with open(TEMP_PATH, "wb") as f:
        writer.write(f)

    POINTS_PER_MM = 2.83465

    print("Joined pdf into paris")
    print(f"    Original pdf size: {width/POINTS_PER_MM:.2f}mm x {height/POINTS_PER_MM:.2f}mm")
    print(f"    New pdf size: {new_width/POINTS_PER_MM:.2f}mm x {height/POINTS_PER_MM:.2f}mm")


shutil.copy(TEMP_PATH, output_path)
os.remove(TEMP_PATH)