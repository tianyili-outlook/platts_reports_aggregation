import fitz
import os
import io

def get_news_toc(doc, thres = 30):
    # new logic: do not want the deepest level toc
    # and get all other items with length > thres
    toc = doc.get_toc()
    new = []
    deepest_level = 0
    for c in toc:
        deepest_level = max(deepest_level, c[0])
    for c in toc:
        if c[0] != deepest_level and len(c[1]) >= thres:
            c[0] = 2
            c[1] = c[1].replace('\n', '')
            new.append(c)
    return new

def combine_pdf():
    toc_list = []
    doc = fitz.open()
    files = os.listdir()
    cur_page = 1
    for file in files:
        if file.startswith('LNG_') and file.endswith('.pdf'):
        	date = file[4:12]
        	toc_list.append([1, 'LNG Daily', cur_page])
        	doc1 = fitz.open(file)
        	toc_list += get_news_toc(doc1)
        	doc.insert_pdf(doc1)
        	cur_page += len(doc1)
    for file in files:
        if file.startswith('GD_') and file.endswith('.pdf'):
            toc_list.append([1, 'Gas Daily', cur_page])
            doc1 = fitz.open(file)
            toc_to_append = get_news_toc(doc1)
            for c in toc_to_append:
                c[2] += cur_page - 1
            toc_list += toc_to_append
            doc.insert_pdf(doc1)
            cur_page += len(doc1)
    for file in files:
        if file.startswith('EGD_') and file.endswith('.pdf'):
            toc_list.append([1, 'European Gas Daily', cur_page])
            doc1 = fitz.open(file)
            toc_to_append = get_news_toc(doc1)
            for c in toc_to_append:
                c[2] += cur_page - 1
            toc_list += toc_to_append
            doc.insert_pdf(doc1)
            cur_page += len(doc1)
    for file in files:
        if file.startswith('EUPD_') and file.endswith('.pdf'):
            toc_list.append([1, 'European Power Daily', cur_page])
            doc1 = fitz.open(file)
            toc_to_append = get_news_toc(doc1)
            for c in toc_to_append:
                c[2] += cur_page - 1
            toc_list += toc_to_append
            doc.insert_pdf(doc1)
            cur_page += len(doc1)
    return doc, toc_list, date

def add_toc_page(doc, toc_list):
    HTML = ''
    level1_counter = 1
    for item in toc_list:
        if item[0] == 1:
            level2_counter = 1
            HTML += ('</ul></li><li><a href>' + str(level1_counter) + ' ' + item[1] 
                     + '</a><ul>')
            level1_counter += 1
        else:
            HTML += ('<li><a href>' + str(level1_counter - 1) + '.' + str(level2_counter) 
                    + ' ' + item[1] + '</a></li>')
            level2_counter += 1
    HTML =  '''
            <div id="toc_container">
            <p class="toc_title">Contents</p>
            <ul class="toc_list">
            ''' + HTML[10:] + '</ul></li></ul></div>'
    
    CSS = """
            #toc_container {
                background: #f9f9f9 none repeat scroll 0 0;

                display: table;
                font-size: 95%;
                margin-bottom: 1em;
                padding: 20px;
                width: auto;
            }

            .toc_title {
                font-weight: 700;
                text-align: center;
            }

            #toc_container li, #toc_container ul, #toc_container ul li{
                list-style: outside none none !important;
            }
          """
    story = fitz.Story(html=HTML, user_css=CSS)
    MEDIABOX = fitz.paper_rect("letter")  # chosen page size
    WHERE = MEDIABOX + (36, 36, -36, -36)  # sub rectangle for source content
    fileptr = io.BytesIO()
    writer = fitz.DocumentWriter(fileptr)
    i = 1
    more = 1
    while more:
        device = writer.begin_page(MEDIABOX)
        more, filled = story.place(WHERE)
        story.draw(device, None)
        writer.end_page()
        i += 1
    writer.close()
    doc1 = fitz.open('pdf', fileptr)
    old_count = doc.page_count
    doc.insert_pdf(doc1)
    new_range = range(old_count, doc.page_count)
    pages = [doc[i] for i in new_range]
    for item in toc_list:  # search for TOC item text to get its rectangle
        for page in pages:
            rl = page.search_for(item[1], flags=~fitz.TEXT_PRESERVE_LIGATURES)
            if rl != []:  # this text must be on next page
                break
        if rl != []:
            rect = rl[0]  # rectangle of TOC item text
            link = {  # make a link from it
                "kind": fitz.LINK_GOTO,
                "from": rect,
                "page": item[2] - 1
            }
            page.insert_link(link)
    for i in new_range:
        doc.move_page(doc.page_count - 1, 0)
    return doc

if __name__ == "__main__":
	doc, toc_list, date = combine_pdf()
	doc = add_toc_page(doc, toc_list)
	doc.ez_save('PlattsReports_' + date + '.pdf')
