"""
    -*- coding: utf-8 -*-
    This script is written in python 3 for both Applle and Windows machines
    written by Jonathan Gomez Martinez (December 2017)
    modified  by Gabriel Wang (February 2018) 
    modified by Jian Chen (Jan 2019)
    modified by Roberto Franzosi (January 2019)
    modified by Jack Hester (January 2019)

    This procedure takes *.txt files and runs StanfordCoreNLP to produce ConLL files for each individual file.
    It then creates a merged ConLL file including all of the ConLL tables in a single ConLL file

    arguments:
        Stanford Core NLP Path: The first argment is the installlation path of stanford corenlp package
        Corpus TXT files Path: The second argument should be the path to the *.txt files.
        Filename/Output path
            The third argument can be a specific file name in the Corpus TXT files Path or the OutputPath
        OutputPath: The third argument should be the folder where the user would like his/her ConLL files saved
        Memory: The fourth argument should be an integer value (1, 2, 3, 4, 5; try 4 first) specifying how much memory (RAM) a user is willing to give to CoreNLP
            More memory can lead to quicker runtime on large *.txt files
        mergeFiles: A boolean specifying whether or not to run the merge algorithm with 1 meaning yes and 0 meaning no
        getDate: A boolean specifying whether or not to run the date grabbing algorithm with 1 meaning yes and 0 meaning no
            Required parameter if running merge files algorithm
        Separator: A specified separator in the file name that indicates the start of a date (e.g., The New York Times_12-21-1878; the separator is _)
            Required parameter if running date grabbing algorithm
        DateFieldLocation: The date start location (e.g., The New York Times_12-21-1878 the date DateFieldLocation is 2; the second field in the file with fields separated by _; 
                The New York Times_Page 1_12-21-1878 the date start location is 3)
            Required parameter if running date grabbing algorithm
        DateFormat: The date format provided
            Date formats: mm-dd-yyyy; m-d-yyyy; dd-mm-yyyy; yyyy-mm-dd; yyyy-dd-mm; yyyy-mm; yyyy;
            Required parameter if running date grabbing algorithm
    
    TODO: Modify the all-files-in-dir mode & one-file mode, the current version is really bad practice
    Useful debug tip: well, you may be in trouble if you are trying to debug the arguments
    But just start with enumerating the sys.argv

    Command prompt start
    
    cd "C:\\Program files (x86)\\PC-ACE\\NLP\\CoreNLP"

    "" around paths are necessaryy when the path includes spaces

    Python StanfordCoreNLP.py "C:\\Program files (x86)\\PC-ACE\\NLP\\stanford-corenlp-full-2018-02-27" "C:\\Users\rfranzo\\Documents\\ACCESS Databases\\PC-ACE\\NEW\\DATA\\CORPUS DATA\\Sample txt" "C:\\Users\rfranzo\\Desktop\\NLP_output" 4 1 1 _ 1 3

"""

from pycorenlp import StanfordCoreNLP
import os
import glob
import time
import datetime
import pandas as pd
import subprocess
import sys
import numpy as np
import io
import re
from collections import OrderedDict
from unidecode import unidecode
import socket
from contextlib import closing
import ntpath
import random
from tkinter import filedialog
import tkinter.messagebox as mb
import tkinter as tk
from tkinter import DISABLED

def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        
        """
        if sock.connect_ex((host, port)) == 0:
            print ("Port is open")
        else:
            print ("Port is not open")
        """

def get_open_port():
    # function to find a open port on local host
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def RunCoreNLP(stanford_core_nlp_path, input_path, output_path, assigned_memory, merge_file_flag,get_date_flag=0,sep='_',date_field_position=3,date_format='mm-dd-yyyy',file_name=''):
    check_socket('localhost',9000)
    port = get_open_port() #find a open port for corenlp
    
    stanford_core_nlp_path = os.path.join(stanford_core_nlp_path,'*')
    
    #TODO: modify this later
    #should be input path, need to talk about this later
    is_path = os.path.isdir(output_path)
    

    #Check that the input directory contains txt files; exit otherwise
    if len(glob.glob(os.path.join(input_path,"*.txt")))==0:
        print ("There are no txt files in the input directory " + str(Path) + ". Program will exit.")
        sys.exit(0)

    command = ['java','-mx'+str(assigned_memory)+'g','-cp', str(stanford_core_nlp_path),'edu.stanford.nlp.pipeline.StanfordCoreNLPServer', '-port', str(port),'timeout','999999']
    #Launch CoreNLP server, allowing us to run *.txt files without re-initializing CoreNLP
    with open(os.devnull, 'w') as fp:
        server = subprocess.Popen(command, stdout=fp) #avoid printing the entire document
        #server = subprocess.Popen(command)  #this will print the entire document
    time.sleep(5)#wait for the subprocess to set up the server

    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        print ("")
        sys.exit(0)

    nlp = StanfordCoreNLP('http://localhost:'+str(port))  #Attach the server to a variable for cleaner code
    #nlp = StanfordCoreNLP('http://localhost:8080')  #Attach the server to a variable for cleaner code

    if(is_path): #This is the all-files-in-dir mode
        InputDocs=[]
        for f in os.listdir(input_path):
            if not f[:2] == '~$': # ignore the temporary files
                if f[-4::]=='.txt':# check if it is a .txt file
                    InputDocs.append(os.path.join(input_path,f))
    else: # one-file mode
        InputDocs = [os.path.join(input_path,file_name)]
    
    startTime = time.localtime()
    print("")
    print("Started running Stanford CoreNLP at " + str(startTime[3]) + ':' + str(startTime[4])) #Prints start time for future reference

    #The loop below opens each *.txt file in the input directory and passes the text to our local CoreNLP server.
    #   The server then returns our ConLL table in a tab separated format which is then saved as a *.ConLL file
    #   Opened files are closed as soon as they are no longer necessary to free-up resources
    i = 0.0
    CorrectlyProcessedFileNames = []
    for file in InputDocs:
        server.poll()
        F = io.open(file, 'r', encoding='utf-8',errors='ignore')
        text = F.read()
        text = text.encode('utf-8')
        #print(text)
        F.close()
        # x: ntpath
        #x = file[len(Path)::] # Only keep the file name with .txt
        #print ("......",x, ntpath.dirname(file),ntpath.basename(file))
        x = ntpath.basename(file)

        #CorrectlyProcessedFileNames.append(x)
        print("")
        print("Parsing file: " + x)
        print("")
        #print(x.find('_'))
        try:
            udata = text.decode("utf-8")
            text = udata.encode("ascii", "ignore")
            #print (text)
            output = nlp.annotate(text.decode('utf-8'), properties={        #Passes text and preferences (properties) to CoreNLP
                'annotators': 'tokenize,ssplit,pos,lemma, ner,parse',
                'outputFormat': 'conll',
                'timeout': '999999',
                'outputDirectory': output_path,
                'replaceExtension': True
            })
           # print(output)
            # Replace normalized paranthese back
            output = str(output).replace("-LRB-","(").replace("-lrb-","(") .replace("-RRB-",")") .replace("-rrb-",")") .replace("-LCB-","{") .replace("-lcb-","{") .replace("-RCB-","}") .replace("-rcb-","}") .replace("-LSB-","[") .replace("-lsb-","[") .replace("-RSB-","]") .replace("-rsb-","]") 

            print("Writing CoNLL table: " + x)
            text_file = io.open(os.path.join(output_path,x) + ".conll", "w", encoding='utf-8')
            text_file.write(output)             #Output *.ConLL file
            text_file.close()
            print(str(100 * round(float(i) / len(InputDocs), 2)) + "% Complete") #Rough progress bar for reference mid-run
            CorrectlyProcessedFileNames.append(x)
            i += 1
        except Exception as e:
            print("")
            print("Could not create CoNLL table for " + "\""+x+"\""+'. Message returned by Stanford server: '+"\""+str(e)+"\"")
            print("")
            server.poll()
    endTime = time.localtime()

    server.kill() #Server is killed before entire procedure is completed since we no longer need it
    print("")
    print("Finished running Stanford CoreNLP at " + str(endTime[3]) + ':' + str(endTime[4]))    #Time when ConLL tables finished computing, for future reference

    if (len(CorrectlyProcessedFileNames) ==0):
        print(str(len(InputDocs)) + " input documents were processed. No CoNLL table was produced! Program will exit.")
        sys.exit(0)

    #Here we merge all of the previously computed ConLL tables into a single merged ConLL table
    ConLL = glob.glob(os.path.join(output_path,"*.conll"))   #Produce a list of ConLL tables in the output directory

    #The loop below opens each *.ConLL file in the ouput directory, checks that the name corresponds to the processed txt filename (excluuding all other CoNLL tables)
    #   and pulls the contents into memory, creating a running table of concatenated tables. Opened files are closed after being pulled into memory 
    #   to preserve resources

    if merge_file_flag == 1:
        startTime = time.localtime()
        print ("")
        print("Started merging at " + str(startTime[3]) + ':' + str(startTime[4]))  #Time when merge started, for future reference
        merge = None    #Initialize an empty variable to assure the  new merged table is in fact new
        MergedDocNum = 1 #the N input documents in the merged CoNLL table are numbered 1 through N
        for table in ConLL:
            lineNum = 1
            x = ntpath.basename(table)[:-6] #get the table name without .CoNLL so that the name can be compared with input document name

            if x in CorrectlyProcessedFileNames:
                print("")
                print("Merging table: " + x)    #Prints the name of the table being worked on
                print("")
                if get_date_flag == 1:
                    startSearch = 0
                    iteration = 0
                    while iteration < date_field_position-1:
                        startSearch = x.find(sep, startSearch + 1) 
                        iteration += 1
                    altSeparator=".txt"
                    end = x.find(sep, startSearch + 1)
                    if end == -1:
                        end = x.find(altSeparator, startSearch + 1)

                    raw_date = x[startSearch+1:end]

                    #https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
                    #the strptime command (strptime(date_string, format) takes date_string and formats it according to format where format has the following values:
                    # %m 09 %-m 9 (does not work on all platforms); %d 07 %-d 7 (does not work on all platforms);
                    #loop through INPUT date formats and change format to Python style
                    print('DATEFORMAT',date_format)
                    
                    try:
                        if date_format == 'mm-dd-yyyy':
                            print('!')
                            date = datetime.datetime.strptime(raw_date, '%m-%d-%Y')
                            dateStr = date.strftime('%m-%d-%Y')
                        elif date_format == 'm-d-yyyy':
                            date = datetime.datetime.strptime(raw_date, '%m-%d-%Y')
                            dateStr = date.strftime('%m-%d-%Y')
                        elif date_format == 'dd-mm-yyyy':
                            date = datetime.datetime.strptime(raw_date, '%d-%m-%Y')
                            dateStr = date.strftime('%d-%m-%Y')
                        elif date_format == 'yyyy-mm-dd':
                            date = datetime.datetime.strptime(raw_date, '%Y-%m-%d')
                            dateStr = date.strftime('%Y-%m-%d')
                        elif date_format == 'yyyy-dd-mm':
                            date = datetime.datetime.strptime(raw_date, '%Y-%d-%m')
                            dateStr = date.strftime('%Y-%d-%m')
                        elif date_format == 'yyyy-mm':
                            date = datetime.datetime.strptime(raw_date, '%Y-%m')
                            dateStr = date.strftime('%Y-%m')
                        elif date_format == 'yyyy':
                            date = datetime.datetime.strptime(raw_date, '%Y')
                            dateStr = date.strftime('%Y')
                    except ValueError:
                        print('Error: You might have provided the incorrect date format or the date (' + raw_date + ') in the filename is wrong. Please check!')
                        pass

                    if x == 'mergedConllTables': #Assures that the merged ConLL table is not merged into our new merged ConLL table (in the case of re-running script)
                        continue
                    if merge is None:
                        hold = pd.DataFrame.from_csv(io.open(table, 'rb'), sep='\t', header=None, index_col=False)
                        holdDocNum = pd.DataFrame(OrderedDict( (('MergedDocNum', np.ones(hold.shape[0]) * MergedDocNum) , ('name', x), ('date', date))) )
                        hold = hold.merge(holdDocNum, left_index=True, right_index=True, how='inner')
                        merge = hold
                    else:
                        hold = pd.DataFrame.from_csv(io.open(table, 'rb'), sep='\t', header=None, index_col=False)
                        holdDocNum = pd.DataFrame(OrderedDict( (('MergedDocNum', np.ones(hold.shape[0]) * MergedDocNum) , ('name', x), ('date', date))) )
                        hold = hold.merge(holdDocNum, left_index=True, right_index=True, how='inner')
                        merge = pd.concat([merge, hold], axis=0, ignore_index=True)
                    MergedDocNum += 1
                if get_date_flag == 0:
                    if x == 'mergedConllTables': #Assures that the merged ConLL table is not merged into our new merged ConLL table (in the case of re-running script)
                        continue
                    if merge is None:
                        hold = pd.DataFrame.from_csv(io.open(table, 'rb'), sep='\t', header=None, index_col=False)
                        holdDocNum = pd.DataFrame(OrderedDict((('DocNum', np.ones(hold.shape[0]) * MergedDocNum), ('name', x))))
                        hold = hold.merge(holdDocNum, left_index=True, right_index=True, how='inner')
                        merge = hold
                    else:
                        hold = pd.DataFrame.from_csv(io.open(table, 'rb'), sep='\t', header=None, index_col=False)
                        holdDocNum = pd.DataFrame(
                            OrderedDict((('DocNum', np.ones(hold.shape[0]) * MergedDocNum), ('name', x))))
                        hold = hold.merge(holdDocNum, left_index=True, right_index=True, how='inner')
                        merge = pd.concat([merge, hold], axis=0, ignore_index=True)
                    MergedDocNum += 1

        MergedDocNum -= 1 
        if MergedDocNum == 0: #no tables were merged
            if (len(ConLL) !=0): #there are CoNLL tables in the output directory
                print("Although there are " + str(len(ConLL)) + " CoNLL tables in your output directory, nore are CoNLL tables for the input txt documents. No merged table produced.")
                sys.exit(0)
            else:
                print ("No CoNLL tables produced for the input txt documents. No merged table produced.")
                sys.exit(0)

        counter = np.arange(1,merge.shape[0]+1)
        merge.insert(7, 'RecordNum', counter)
        sentenceID = 0
        docID = 1
        sentIDs = []
        for i in range(merge.shape[0]):
            if int(merge.iloc[i][8]) > docID:
               docID = docID + 1
               sentenceID = 0
            if(str(merge.iloc[i][0]) == '1'):
                sentenceID += 1
            sentIDs.append(sentenceID)
        merge.insert(9, 'SentenceID', sentIDs)
        merge.to_csv(os.path.join(output_path,"mergedConllTables.conll"), sep='\t', index=False, header=False)    #Outputs merged ConLL table as a *.ConLL file into our output directory
        endTime = time.localtime()
        print("")
        print("Finished merging CoNLL tables at " + str(endTime[3]) + ':' + str(endTime[4]))     #Time when merge finished, for future reference
        
        return
    
#%%
text_label = """For information about this program, hit \"Read Me\"\nTo run the program, select the Stanford CoreNLP and corpus txt files paths and hit buttons below.\nTo exit the program, hit \"Quit\""""

introduction_main = """reserved for introduction"""

#%%
"""
########################
            GUI
#######################
"""
queries_x_cord = 120


label_x_cord = 342
label_x_cord_wn = 375

help_button_x_cord = 50
labels_x_cord = 150
entry_box_x_cord = 350
basic_y_cord = 90
y_step = 40

def exit_window():
    global window
    window.destroy()
    exit()
    
def empty():
    print('empty function for debug')
    return 

"""
msgboxes
"""
def main_msgbox():
    mb.showinfo(title='Introduction', message=introduction_main)
    
def helper_buttons(canvas,x_cord,y_cord,text_title,text_msg):
    
    def msg_box():
        mb.showinfo(title=text_title, message=text_msg)
    tk.Button(canvas, text='? HELP', command=msg_box).place(x=x_cord,y=y_cord)

"""
button-associated functions
"""
def select_output_dir():
    global output_file_path
    
    file_path = filedialog.askdirectory(initialdir = os.getcwd())
    output_file_path.set(file_path)
    print(file_path)
    return file_path

def select_stanford_corenlp_dir():
    global stanford_core_NLP_path
    
    file_path = filedialog.askdirectory(initialdir = os.getcwd())
    stanford_core_NLP_path.set(file_path)
    print(file_path)
    return file_path

def select_input_path():
    global input_file_path
    file_path = filedialog.askdirectory(initialdir = os.getcwd())
    input_file_path.set(file_path)
    print(file_path)
    return file_path

def memory_dropdown():
    print(assigned_memory.get())

def test_input_and_run_query():
    
    CoreNLPPath = stanford_core_NLP_path.get()
    
    Path = input_file_path.get()
    
    Output = output_file_path.get()
    
    mem = memory_var.get()
    
    mergeFiles = merge_file_or_not.get()
    
    getDate = find_date_or_not.get()
    
    separator = separator_var.get()
    
    DateFieldLocation = date_loc_var.get()
    
    DateFormat = date_format.get()
    
    print(CoreNLPPath, Path, Output,mem,mergeFiles,getDate,separator,DateFieldLocation,DateFormat)
    
    RunCoreNLP(CoreNLPPath, Path, Output,mem,mergeFiles,getDate,separator,DateFieldLocation,DateFormat)
    return

window = tk.Tk()
window.title('Noun and Verb Analysis')
window.geometry('1000x600')

"""
variables
"""
global stanford_core_NLP_path, input_file_path,output_file_path,memory_var,separator_var,date_loc_var,date_format,find_date_or_not,merge_file_or_not

stanford_core_NLP_path = tk.StringVar()
stanford_core_NLP_path.set('')

input_file_path = tk.StringVar()
input_file_path.set('')

output_file_path = tk.StringVar()
output_file_path.set('')

memory_var = tk.IntVar()
memory_var.set(4)

separator_var = tk.StringVar()
separator_var.set('_')

date_loc_var = tk.IntVar()
date_loc_var.set(3)

date_format = tk.StringVar()
date_format.set('mm-dd-yyyy')




# Create a Tkinter variable



#For more information about a specific button, hit the \"? HELP\" button next to it.

intro = tk.Label(window, 
                 anchor = 'w',
                 text=text_label)
intro.pack()


quit_button = tk.Button(window, text='QUIT', width=20,height=2, command=exit_window)
quit_button.place(x=550,y=500)

execute_button = tk.Button(window, text='Execute StanfordCoreNLP', width=20,height=2, command=test_input_and_run_query)
execute_button.place(x=350,y=500)

intro_button = tk.Button(window, text='Read Me',command=main_msgbox,width=20,height=2)
intro_button.place(x=150,y=500)


select_input_dir_button=tk.Button(window, width = 22,text='select CoreNLP file directory', command=select_stanford_corenlp_dir)
select_input_dir_button.place(x=queries_x_cord,y=basic_y_cord)
tk.Label(window, textvariable=stanford_core_NLP_path).place(x=label_x_cord, y= basic_y_cord)

select_input_dir_button=tk.Button(window, width = 22,text='select INPUT file directory', command=select_input_path)
select_input_dir_button.place(x=queries_x_cord,y=basic_y_cord+y_step)
tk.Label(window, textvariable=input_file_path).place(x=label_x_cord, y= basic_y_cord+y_step)

select_save_file_button=tk.Button(window, width = 22,text='select OUTPUT file directory', command=select_output_dir)
select_save_file_button.place(x=queries_x_cord,y=basic_y_cord+y_step*2)
tk.Label(window, textvariable=output_file_path).place(x=label_x_cord, y= basic_y_cord+y_step*2)

"""
check box
"""
def print_checkboxes():
    if merge_file_or_not.get() == 1:
        merge_file_checkbox_msg.config(text="A merged CoNLL table will be produced")
    elif merge_file_or_not.get() == 0:
        merge_file_checkbox_msg.config(text="No merged CoNLL table will be produced")

    if find_date_or_not.get() == 1:
        find_date_checkbox_msg.config(text="Date Option On.")
        date_format_menu.configure(state="normal")
        entry_sep.configure(state="normal")
        loc_menu.configure(state='normal')
    elif find_date_or_not.get() == 0:
        find_date_checkbox_msg.config(text="Date Option Off.")
        date_format_menu.configure(state="disabled")
        entry_sep.configure(state="disabled")
        loc_menu.configure(state="disabled")
        #w.config(state=DISABLED)
        
    

merge_file_checkbox_msg = tk.Label(window, text='A merged CoNLL table will be produced.')
merge_file_checkbox_msg.place(x=label_x_cord_wn,y=basic_y_cord+y_step*3)
merge_file_or_not = tk.IntVar()
merge_file_or_not.set(1)
merge_file_checkbox = tk.Checkbutton(window, text='Merge CoNLL tables?', variable=merge_file_or_not, onvalue=1, offvalue=0,
                    command=print_checkboxes)
merge_file_checkbox.place(x=queries_x_cord,y=basic_y_cord+y_step*3)
merge_file_checkbox_msg.place(x=label_x_cord,y=basic_y_cord+y_step*3)

find_date_checkbox_msg = tk.Label(window, text='Date Option Off.')
find_date_checkbox_msg.place(x=label_x_cord_wn,y=basic_y_cord+y_step*5)
find_date_or_not = tk.IntVar()
find_date_or_not.set(0)
find_date_checkbox = tk.Checkbutton(window, text='Find Date?', variable=find_date_or_not, onvalue=1, offvalue=0,
                    command=print_checkboxes)
find_date_checkbox.place(x=queries_x_cord,y=basic_y_cord+y_step*5)
find_date_checkbox_msg.place(x=label_x_cord,y=basic_y_cord+y_step*5)

date_format_lb = tk.Label(window,text='Date Format: ')
date_format_lb.place(x=queries_x_cord,y=basic_y_cord+y_step*6)
date_format_menu = tk.OptionMenu(window, date_format, 'mm-dd-yyyy', 'm-d-yyyy', 'dd-mm-yyyy','yyyy-mm-dd','yyyy-dd-mm','yyyy-mm','yyyy')
date_format_menu.configure(width=10)
date_format_menu.place(x=label_x_cord, y = basic_y_cord+y_step*6)
if find_date_or_not.get() == 0:
    date_format_menu.configure(state='disabled')    

mem_menu_lb = tk.Label(window, text='Memory Option: ')
mem_menu_lb.place(x=queries_x_cord, y = basic_y_cord+y_step*4)
mem_menu = tk.OptionMenu(window,memory_var,1,2,3,4)
mem_menu.configure(width=10)
mem_menu.place(x=label_x_cord,y=basic_y_cord+y_step*4)

entry_sep_lb = tk.Label(window, text='Date Separator: ')
entry_sep_lb.place(x=queries_x_cord, y = basic_y_cord+y_step*7)
entry_sep = tk.Entry(window, textvariable=separator_var)
entry_sep.place(x=label_x_cord,y=basic_y_cord+y_step*7)
if find_date_or_not.get() == 0:
    entry_sep.configure(state='disabled') 
    
loc_menu_lb = tk.Label(window, text='Date Position: ')
loc_menu_lb.place(x=queries_x_cord, y = basic_y_cord+y_step*8)
loc_menu = tk.OptionMenu(window,date_loc_var,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30)
loc_menu.configure(width=10)
loc_menu.place(x=label_x_cord,y=basic_y_cord+y_step*8)
if find_date_or_not.get() == 0:
    loc_menu.configure(state='disabled') 



"""
MAJOR BUTTONS
"""
try:
    
    CoreNLPPath = sys.argv[1]
    Path = sys.argv[2]
    # if the third argument is a path, then it is output path
    # else it is the specific input file
    is_path = os.path.isdir(sys.argv[3]) 

    if is_path:
        outputPath = sys.argv[3]
        mem = sys.argv[4]
        mergeFiles = sys.argv[5]
        mergeFiles = int(mergeFiles)
        if mergeFiles == 1:
            getDate = sys.argv[6]
            getDate = int(getDate)
            if getDate == 1:
                separator = sys.argv[7]
                DateFieldLocation = sys.argv[8]
                DateFieldLocation = int(DateFieldLocation)
                DateFormat = str(sys.argv[9])
        RunCoreNLP(CoreNLPPath, Path, Output,mem,mergeFiles,getDate,separator,DateFieldLocation,DateFormat)
    else:
        filename = sys.argv[3]
        outputPath = sys.argv[4]
        mem = sys.argv[5]
        mergeFiles = sys.argv[6]
        mergeFiles = int(mergeFiles)
        if mergeFiles == 1:
            getDate = sys.argv[7]
            getDate = int(getDate)
            if getDate == 1:
                separator = sys.argv[8]
                DateFieldLocation = sys.argv[9]
                DateFieldLocation = int(DateFieldLocation)
                DateFormat = str(sys.argv[10])
    RunCoreNLP(CoreNLPPath, Path, Output,mem,mergeFiles,getDate,separator,DateFieldLocation,DateFormat,filename)
    
except Exception as e:
    print ("\nCommand line arguments are empty, incorrect, or out of order, ERROR: "+e.__doc__)
    print ("\nGraphical User Interface will be activated")   
    window.mainloop()
        