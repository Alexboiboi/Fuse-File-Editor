# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
import sys
import os
import difflib

import ipywidgets as widgets
from IPython.display import display, FileLink

def process_data(data,
                 header_length = 7,
                 lsb_insert_start_position = 66,
                 skip_last_rows = 2,
                 hex_recurrence = 4,
                 bin_string_to_insert = '0000'):
    '''reads fuse file and inserts a binary number at desired position. lsb insert start postion is counted from right to left.
    String to insert is inserted from left to right
    '''
    filename, header, body = read_lines(data)
    nol = 0
    for ind,line in enumerate(body[:-skip_last_rows:hex_recurrence]):
        nol+=1
        hex_number = line.replace('\n','') # remove line break from string
        numbs = process_hex(hex_number, lsb_insert_start_position, bin_string_to_insert)
        body[hex_recurrence*ind] =   numbs['hex_number_modified'] + '\n' # add line break

    name, ext  = os.path.splitext(filename)
    new_filename = name+f'_processed_lsb_insert_start_position_{lsb_insert_start_position}'+ext
    with open(new_filename, 'w') as the_file:
        the_file.write(''.join(header))
        the_file.write(''.join(body))
    
    print(f'Done with {nol} lines processed, lsb start position={lsb_insert_start_position}')
    return new_filename

def read_lines(data, header_length=7):
    try:
        assert os.path.isfile(data), 'file not found'
        assert os.path.splitext(data)[1]=='.fuse', 'not a valid file, must be a fuse file'
        filename = data
    except:
        filename = data.metadata[0]['name']
        with open(filename, "wb") as fp:
            fp.write(data.data[0])
            
    with open(filename,'r') as fin:
        lines = fin.readlines()
        
    header = lines[:header_length]
    body = lines[header_length:]
    return filename, header, body

def process_hex(hex_number,
                lsb_insert_start_position = 66,
                bin_string_to_insert = '0000'):
    
    bin_number = f'{int(hex_number, base=16):092b}' # binary string must be 92 chars long
    bin_number_modified = bin_number[:-lsb_insert_start_position+1] \
                          + bin_string_to_insert \
                          + bin_number[-lsb_insert_start_position+1:]
    hex_number_modified = f'{int(bin_number_modified, base=2):024X}' #hex has 24 chars

    return {'hex_number':hex_number,
            'hex_number_modified':hex_number_modified,
            'bin_number':bin_number,
            'bin_number_modified':bin_number_modified}
            

if __name__== "__main__":
    try:
        process_data(sys.argv[1])
    except:
        process_data(filename)


# %%
def update_diff(data, preview_num=5, hex_recurrence=4, header_length=7, skip_last_rows=2, **kwargs):
    filename, header, body = read_lines(data, header_length=header_length)
    lines = body[:-skip_last_rows:hex_recurrence]
    numbs = [process_hex(l.replace('\n',''), **kwargs) for l in lines[:preview_num]]
    b1 = [n['bin_number'] for n in numbs]
    b2 = [n['bin_number_modified'] for n in numbs]
    h1 = [n['hex_number'] for n in numbs]
    h2 = [n['hex_number_modified'] for n in numbs]
    bdiff.value = difflib.HtmlDiff().make_file(b1[0] if preview_num==1 else b1, b2[0] if preview_num==1 else b2)
    hdiff.value = difflib.HtmlDiff().make_file(h1[0] if preview_num==1 else h1, h2[0] if preview_num==1 else h2)


# %%
w_opts = dict(
    header_length = widgets.IntText(value=7,style=dict(description_width='150px')),
    lsb_insert_start_position = widgets.IntText(value=66,style=dict(description_width='150px')),
    skip_last_rows = widgets.IntText(value=2,style=dict(description_width='150px')),
    hex_recurrence = widgets.IntText(value=4,style=dict(description_width='150px')),
    bin_string_to_insert = widgets.Text(value='0000',style=dict(description_width='150px')),
    preview_num = widgets.BoundedIntText(value=5, min=1, max=20, style=dict(description_width='150px')),
)

options_widgets = widgets.VBox(list(w_opts.values()))

bdiff = widgets.HTML()
hdiff = widgets.HTML()
diff_widgets = widgets.Accordion([widgets.HBox([bdiff,hdiff], layout=dict(flex_flow='wrap'))])
diff_widgets.set_title(0,'Preview')

w = widgets.interactive(update_diff, data=widgets.fixed(filename), **w_opts)
w.update()


# %%
file_download_widget = widgets.Output()

w_opts = dict(
    header_length = widgets.IntText(value=7,style=dict(description_width='150px')),
    lsb_insert_start_position = widgets.IntText(value=66,style=dict(description_width='150px')),
    skip_last_rows = widgets.IntText(value=2,style=dict(description_width='150px')),
    hex_recurrence = widgets.IntText(value=4,style=dict(description_width='150px')),
    bin_string_to_insert = widgets.Text(value='0000',style=dict(description_width='150px')),
)
uploader = widgets.FileUpload(
    description = 'Upload fuse file',
    button_style = 'primary',
    accept='.fuse',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False,  # True to accept multiple files upload else False
)
uploader_text = widgets.HTML()
uploader_container = widgets.HBox([uploader, uploader_text])

def _on_processed_btn_clicked(b):
    file_download_widget.clear_output()
    with file_download_widget:
        write_file(**{k:v.value for k,v in w_opts.items()})
process_btn = widgets.Button(description='proceed and write file', button_style='success', layout=dict(width='auto'))
process_btn.on_click(_on_processed_btn_clicked)

def write_file(**kwargs):
    new_filename = process_data(filename, **kwargs)
    local_file = FileLink(new_filename, result_html_prefix="Click here to download: ")
    display(local_file)


# %%
def on_upload(change):
    app_contents.children = [uploader_container, options_widgets, diff_widgets, process_btn, file_download_widget]
    uploader_text.value = uploader.metadata[0]['name']
    
uploader.observe(on_upload, names='value')
app_contents = widgets.VBox([uploader])   
app_title= widgets.HTML('<h1> Fuse File Editor</h1>')
app = widgets.VBox([app_title, app_contents])
app
