from modeller import *
from modeller.automodel import *
from Bio import PDB as pdb
import re
import csv
import shutil

"""
This program fills in missing residues from (correctly formatted) pdb files.
It reads in the coordinates and detects any missing residues and then
gives an alignment file that can be used for loop modeling. It currently
does not do a very good job, as modeller is both poorly executed and also
I do not have the practical knowlede to make it do exactly what I want.

Known issues: 
    the paths are hard coded, you will need to modify them
    the loop modeling often results in knots, this must be fixed
        before anything else can be done

To do:
    fix issues with knots!
    modify way it reads in sequence so that models are automatically given
        the correct name including active/inactive designation (DONE)
    put in loop to automatically put in regions to modify (now hard coded)
        (CURRENTLY WORKING ON THIS)
    put it in a loop so that it reads the active/inactive templates and then
        create models in a separate directory (DONE)
    put in a sanity check to make sure there are no mutations in the pdb 
        structures (we know there are some) and use modeller to mutate
        these back 
        (ASK JOE ABOUT THIS)
    maybe put in a sanity check at the end that compares models of similar
        sequence or structure
"""

datafile = open('./structures.csv', 'r') #Opens the structures file for reading
datareader = csv.reader(datafile) #reads structures file
data = [] #initializes a list called data
for row in datareader:
    data.append(row) #adds an element to data for each row in structures.csv

#print data[0] 

class PDB_info(object):
    """
    This class is used to assign meaning to specific elements in a given row of the .csv file
    """
    def __init__(self, row):
        self.id = row[0] #id number of the pdb file
        self.protein = row[1] #protein name the pdb file is associated with
        self.complete = row[2] #yes or no?
        self.conformation = row[3] #active or inactive?

pdb_info = [PDB_info(item) for item in data]

#print pdb_info[0].id

for i in range(len(pdb_info)):
    pdb_name = pdb_info[i].id #saves given pdb name as a variable
    protein_name = pdb_info[i].protein #saves given protein name as a variable
    complete = pdb_info[i].complete #saves yes or no for complete
    structure_conf = pdb_info[i].conformation #saves active or inactive for conformation
    print pdb_name
    pdb_file = './PDBs/'+pdb_name+'.pdb'
    fp = open(pdb_file)
    parser = pdb.PDBParser()
    struct = parser.get_structure("name",pdb_file) #read in pdb file using PDBParser
    ppb = pdb.PPBuilder() #peptide class to get sequence
    last = 100000 #make sure first iter through loop has no dashes -
    structure_sequence = ''
    for seq in ppb.build_peptides(struct):
        #use this re to get the chain breaks
        search = re.search('start=([0-9]{1,4}).+end=([0-9]{1,4})',"{0}".format(seq))
        first = search.groups()[0]
        diff = int(first)-int(last)
        if(diff>0): #put in dashes for missing residues
            structure_sequence += diff*'-'
        last = search.groups()[1]
        structure_sequence += seq.get_sequence()
        #print (int(first)-21),(int(last)-21)

    #put in newlines into structure_sequence for proper PIR format
    for i in range(0,len(structure_sequence),70):
        structure_sequence = structure_sequence[:i] + "\n" + structure_sequence[i:]

    #read in the full sequence from the pdb file
    full_sequence = ''
    lines = fp.readlines()
    first = lines[0]
    header = re.split('HEADER\W+',first)[1]
    for index in range(1,10):
        split_line = re.split('REMARK 300 ',lines[index])
        if split_line[0] == '':
            full_sequence += split_line[1]


    #write the alignment file

    pdb_code = (pdb_name.split("-"[0])) 
    name = pdb_code[0] #changed this from hard coded 4F7S; it does not seem like this variable is used anywhere else
    PIR = open('active.ali','w')
    PIR.write(">P1;{0}\n".format(pdb_name))
    PIR.write("structureX:{0}".format(header))
    PIR.write("{0}*\n\n".format(structure_sequence.strip()))
    PIR.write(">P1;{0}\n".format(protein_name))
    PIR.write("sequence:{0}".format(header))
    PIR.write("{0}*\n\n".format(full_sequence.strip()))
    PIR.close()


    #begin modeller stuff here
    log.verbose()
    env = environ()

    #where to look for pdb files
    env.io.atom_files_directory = ['.', './PDBs']

    # Create a new class based on 'loopmodel' so that we can redefine
    # select_loop_atoms
    class MyLoop(automodel):
        # This routine picks the residues to be refined by loop modeling
        def select_loop_atoms(self): #need to fix this
            return selection(self.residue_range('95:', '101:'),
                             self.residue_range('166:', '175:'),
                             self.residue_range('217:', '222:'))

            # index of the last model         
    a = MyLoop(env,
            alnfile  = 'active.ali',      # alignment filename
            knowns   = pdb_name,               # codes of the templates
            sequence = protein_name,               # code of the target
            library_schedule = autosched.slow,
            deviation = 1,
            assess_methods = assess.DOPE) # assess each loop with DOPE
    a.starting_model = 1                 # index of the first model
    a.ending_model  = 1 
    a.make() #do modeling and loop refinement
    if re.match("active", structure_conf) is not None:
        if re.match("yes", complete) is not None:
            shutil.move(protein_name+'.B99990001.pdb', './actives/complete') #where is this PDB file generated in this code?  IMPORTANT TO FIGURE OUT
        if re.match("no", complete) is not None:
            shutil.move(protein_name+'.B99990001.pdb', './actives/incomplete') 
    if re.match("inactive", structure_conf) is not None: #if statement to facilitate change of directory if structure is active; check regex
        if re.match("yes", complete) is not None:
            shutil.move(protein_name+'.B99990001.pdb', './inactives/complete') #where is this PDB file generated in this code?  IMPORTANT TO FIGURE OUT
        if re.match("no", complete) is not None:
            shutil.move(protein_name+'.B99990001.pdb', './inactives/incomplete') 