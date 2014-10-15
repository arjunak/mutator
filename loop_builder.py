from modeller import *
from modeller.automodel import *
from Bio import PDB as pdb
import re

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
        the correct name including active/inactive designation
    put in loop to automatically put in regions to modify (now hard coded)
    put it in a loop so that it reads the active/inactive templates and then
        create models in a separate directory
    put in a sanity check to make sure there are no mutations in the pdb 
        structures (we know there are some) and use modeller to mutate
        these back 
    maybe put in a sanity check at the end that compares models of similar
        sequence or structure
"""

pdb_name='4F7S-A'
protein_name='CDK8'
pdb_file='actives/'+pdb_name+'.pdb'
fp=open(pdb_file)
parser=pdb.PDBParser()
struct=parser.get_structure("name",pdb_file) #read in pdb file using PDBParser
ppb=pdb.PPBuilder() #peptide class to get sequence
last=100000 #make sure first iter through loop has no dashes -
structure_sequence=''
for seq in ppb.build_peptides(struct):
    #use this re to get the chain breaks
    search=re.search('start=([0-9]{1,4}).+end=([0-9]{1,4})',"{0}".format(seq))
    first=search.groups()[0]
    diff=int(first)-int(last)
    if(diff>0): #put in dashes for missing residues
        structure_sequence+=diff*'-'
    last=search.groups()[1]
    structure_sequence+=seq.get_sequence()
    #print (int(first)-21),(int(last)-21)

#put in newlines into structure_sequence for proper PIR format
for i in range(0,len(structure_sequence),70):
    structure_sequence=structure_sequence[:i] + "\n" + structure_sequence[i:]

#read in the full sequence from the pdb file
full_sequence=''
lines=fp.readlines()
first=lines[0]
header=re.split('HEADER\W+',first)[1]
for index in range(1,10):
    split_line=re.split('REMARK 300 ',lines[index])
    if split_line[0]=='':
        full_sequence+=split_line[1]


#write the alignment file
name='4F7S'
PIR=open('active.ali','w')
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
env.io.atom_files_directory = ['.', './actives']

# Create a new class based on 'loopmodel' so that we can redefine
# select_loop_atoms
class MyLoop(automodel):
    # This routine picks the residues to be refined by loop modeling
    def select_loop_atoms(self): #need to fix this
        return selection(self.residue_range('95:', '101:'),
                         self.residue_range('166:', '175:'),
                         self.residue_range('217:', '222:'))

a = MyLoop(env,
           alnfile  = 'active.ali',      # alignment filename
           knowns   = pdb_name,               # codes of the templates
           sequence = protein_name,               # code of the target
           library_schedule = autosched.slow,
           deviation = 1,
           assess_methods=assess.DOPE) # assess each loop with DOPE
a.starting_model= 1                 # index of the first model
a.ending_model  = 1                 # index of the last model

a.make()                            # do modeling and loop refinement