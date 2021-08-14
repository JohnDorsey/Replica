
from collections import namedtuple
import re


def loadFile(filename):
  result = None
  with open(filename,"r") as theFile:
    result = theFile.readlines(65536)
  return "".join(result).replace("\r\n","\n")
  
def loadFileAndCompile(filename, old=None):
  result = compile(loadFile(filename),";","`")
  if result == old:
    print("PyReplicaCompile.loadFileAndCompile: WARNING: no changes!")
  return result



class ReplicaCompileError(ValueError):
  pass
  
class ReplicaLabelError(ReplicaCompileError):
  pass

class ReplicaSyntaxError(ReplicaCompileError):
  pass
  
def replicaSyntaxAssert(inputBool, message):
  if not inputBool:
    raise ReplicaSyntaxError(message)
    
def shortrepr(thing):
  if hasattr(thing,"shortrepr"):
    return thing.shortrepr()
  else:
    return repr(thing)
    
    
class Instruction:
  def __init__(self, name, args, lineNumber, source):
    self.name, self.args, self.lineNumber, self.source = name, args, lineNumber, source
    
  def shortrepr(self):
    return repr(self).replace("PyReplicaCompile.Instruction instance at","Instruction "+self.name)

  def __str__(self):
    argReprStr = "[" + ", ".join(shortrepr(arg) for arg in self.args) + "]"
    result = "{}(name={}, args={}, lineNumber={}, source={})".format(self.shortrepr(), self.name, argReprStr, self.lineNumber, self.source)
    result = result.replace("...","Instruction.__str__: recursion can't be shown.")
    return result


class UnresolvedJump:
  def __init__(self, reference, offset):
    self.reference, self.offset = reference, offset
    self.validate()
    
  def setReference(self,reference):
    self.reference = reference
    self.validate()
    
  def validate(self):
    if isinstance(self.reference, UnresolvedLabel):
      return True
    if isinstance(self.reference, Instruction):
      if self.reference.name == "replace":
        return True
    if self.reference == self:
      return True
    if type(self.reference) == str:
      return True
    assert False, "validation failure: self.reference is {}.".format(repr(self.reference))
    
  #def __repr__(self):
  #  return "<UnresolvedJump pointing to {} with offset {}>".format(self.reference.shortrepr(),self.offset)
  
  def shortrepr(self):
    return repr(self).replace("PyReplicaCompile.UnresolvedJump instance at","UnresolvedJump").replace(">"," to {}+{}>".format(shortrepr(self.reference) if self.reference != self else "itself",self.offset))

  def __str__(self):
    result = "UnresolvedJump(reference={}, offset={})".format(self.reference.shortrepr(), self.offset)
    result = result.replace("...","UnresolvedJump.__str__: recursion can't be shown.")
    return result
    
UnresolvedLabel = namedtuple("UnresolvedLabel",["name"])

"""
class ReplicaCompilableText:
    
  def isMatch(inputText):
    pass
    
  def compileWithContext(self,inputText,allLines,ownIndex):
    pass
"""
    
class ReplicaInstructionCompiler:
    
  def canApply(self,inputInstruction):
    pass
    
  def compileWithContext(self,inputInstruction,allInstructions,ownIndex):
    pass


class ReplicaMatchInstructionCompiler(ReplicaInstructionCompiler):
  def __init__(self):
    self.pat = re.compile("{MATCH .+?}")

  def canApply(self,inputInstruction):
    if inputInstruction.name == "replace":
      if self.pat.findall(inputInstruction.args[0]) or self.pat.findall(inputInstruction.args[1]):
        return True
    return False
    
  def compileWithContext(self,inputInstruction,allInstructions,ownIndex):
    assert self.canApply(inputInstruction)
    raise NotImplementedError()


 
def instructionsToString(instructionsToConvert,delimiter="\n"):
  return delimiter.join(str(instruction) for instruction in instructionsToConvert)
  
def validateInstructions(instructionsToValidate):
  for i,instruction in enumerate(instructionsToValidate):
    if not instruction.name == "replace":
      raise ReplicaCompileError("unacceptable instruction name for instruction at index {}. instruction is:{}".format(i,instruction))
    if not len(instruction.args) == 4:
      raise ReplicaCompileError("unacceptable argument count for instruction at index {}. instruction is:{}".format(i,instruction))
    for argi,currentArg in enumerate(instruction.args):
      if not type(currentArg) == str:
        raise ReplicaCompileError("unacceptable argument type for argument at index {} for instruction at index {}. instruction is:{}".format(argi,i,instruction))
        
def getNextInstructionByName(searchInstructions, searchName, startIndexInclusive=None, endIndexInclusive=None, invert=False):
  for searchIndex in range(startIndexInclusive, min(endIndexInclusive+1, len(searchInstructions))):
    if (searchInstructions[searchIndex].name == searchName) != invert:
      return searchInstructions[searchIndex]
  return None
    
def indexUsingIs(searchList,searchTerm):
  for i,item in enumerate(searchList):
    if item is searchTerm:
      return i
  raise IndexError("couldn't find searchTerm {}.".format(repr(searchTerm)))
  
def formatCompiledLine(lineNumber, line):
  return str(lineNumber).rjust(4,fillchar=".")+": "+str(bin(lineNumber)[2:]).rjust(10,fillchar=".")+": "+line
  
def formatCompiled(dataToFormat,delimiter):
  result = (delimiter+"\n").join(formatCompiledLine(i,line) for i,line in enumerate(dataToFormat.split(";")))
  return result




def compile(inputText,wordDelimiter,argDelimiter):
  inputLines = inputText.split("\n")
  instructions = []
  def NewInstruction(name, args):
    return Instruction(name, args, i, currentLine)
  i = 0
  while i < len(inputLines):
    currentLine = inputLines[i]
    if currentLine.startswith("{LABEL "):
      replicaSyntaxAssert(currentLine.replace(" ","").endswith("}"), "missing curly brace on line {}:\n{}\n".format(i,currentLine))
      instructions.append(NewInstruction("label",[currentLine[7:-1]]))
      i += 1
      continue
    if currentLine.startswith("{JUMP "):
      currentLine = currentLine.replace(" ","")
      replicaSyntaxAssert(currentLine.endswith("}"), "missing curly brace on line {}:\n{}\n".format(i,currentLine))
      instructions.append(NewInstruction("unconditionalJump",[UnresolvedJump(UnresolvedLabel(currentLine[5:-1]),0)]))
      i += 1
      continue
    if currentLine.startswith("{IF SUCCESSFUL JUMP ") and currentLine.endswith("}"):
      instructions.append(NewInstruction("conditionalJump",[UnresolvedJump(UnresolvedLabel(currentLine[20:-1]),0),"placeholder for skipping this instruction"]))
      instructions[-1].args[1] = UnresolvedJump("placeholder for skipping this instruction",1)
      instructions[-1].args[1].setReference(instructions[-1].args[1])
      i += 1
      continue
    if currentLine == "{FIND}":
      instructions.append(NewInstruction("replace",[inputLines[i+1],inputLines[i+1],"PLACEHOLDER FOR OPTIONAL CONDITIONAL JUMP","PLACEHOLDER FOR OPTIONAL CONDITIONAL JUMP"]))
      i += 2
      continue
    if currentLine in ["{REPLACE}","{REPLACE ONCE}"]:
      instructions.append(NewInstruction("replace",[inputLines[i+1],inputLines[i+2],"PLACEHOLDER FOR OPTIONAL CONDITIONAL JUMP","PLACEHOLDER FOR OPTIONAL CONDITIONAL JUMP"]))
      i += 3
      continue
    if currentLine == "{REPLACE FOREVER}":
      checkingReplaceInstruction = NewInstruction("replace",[inputLines[i+1],inputLines[i+2],"placeholder for looping replace instruction","PLACEHOLDER FOR OPTIONAL FAILURE JUMP HERE+2"])
      loopingReplaceInstruction = NewInstruction("replace",[inputLines[i+1],inputLines[i+2],UnresolvedJump("placeholder for this replace instruction",0),"PLACEHOLDER FOR OPTIONAL SUCCESS JUMP HERE+1"])
      checkingReplaceInstruction.args[2] = UnresolvedJump(loopingReplaceInstruction,0)
      checkingReplaceInstruction.args[3] = UnresolvedJump(loopingReplaceInstruction,1) #this won't land on the branch instruction that will be after the loopingReplaceInstruction, because those don't exist anymore by the times jumps are resolved - they are merged into the replace instructions before then.
      loopingReplaceInstruction.args[2].setReference(checkingReplaceInstruction)
      instructions.append(checkingReplaceInstruction)
      instructions.append(loopingReplaceInstruction)
      i += 3
      continue
    if currentLine.replace(" ","") == "" or currentLine.replace(" ","").startswith("//"):
      i += 1
      continue
    raise ReplicaSyntaxError("line {} is invalid:\n{}\n".format(i,currentLine))
    
  #print("\nafter first pass: \n" + instructionsToString(instructions))
  mergeJumpsWithReplaces(instructions)
  #print("\nafter mergeJumpsWithReplaces: \n" + instructionsToString(instructions))
  processUnconditionalJumps(instructions)
  #print("\nafter processUnconditionalJumps: \n" + instructionsToString(instructions))
  resolveLabels(instructions)
  #print("\nafter resolveLabels: \n" + instructionsToString(instructions))
  resolveJumps(instructions)
  #print("\nafter resolveJumps: \n" + instructionsToString(instructions))
  
  
  for instruction in instructions:
    for argi in range(4):
      instruction.args[argi] = instruction.args[argi].replace("{BLANK LINE}","")
  
  validateInstructions(instructions)
  
  return wordDelimiter.join(argDelimiter.join(instruction.args) for instruction in instructions)
    
    
    
   
def mergeJumpsWithReplaces(instructions):
  i = 0
  while i < len(instructions):
    currentInstruction = instructions[i]
    if currentInstruction.name == "replace":
      if currentInstruction.args[2:] == ["PLACEHOLDER FOR OPTIONAL CONDITIONAL JUMP"] * 2:
        nextConditionalJump = getNextInstructionByName(instructions,"conditionalJump",startIndexInclusive=i+1,endIndexInclusive=i+1)
        if nextConditionalJump != None:
          currentInstruction.args[2] = nextConditionalJump.args[0]
          currentInstruction.args[3] = nextConditionalJump.args[1]
        else:
          currentInstruction.args[2] = UnresolvedJump(currentInstruction,1) #set non-branching jumps.
          currentInstruction.args[3] = UnresolvedJump(currentInstruction,1) #set non-branching jumps.
      elif currentInstruction.args[3] in ["PLACEHOLDER FOR OPTIONAL SUCCESS JUMP HERE+1","PLACEHOLDER FOR OPTIONAL FAILURE JUMP HERE+2"]:
        nextConditionalJump = None
        if currentInstruction.args[3] in "PLACEHOLDER FOR OPTIONAL SUCCESS JUMP HERE+1":
          nextConditionalJump = getNextInstructionByName(instructions, "conditionalJump", startIndexInclusive=i+1, endIndexInclusive=i+1)
        elif currentInstruction.args[3] in "PLACEHOLDER FOR OPTIONAL FAILURE JUMP HERE+2":
          nextConditionalJump = getNextInstructionByName(instructions, "conditionalJump", startIndexInclusive=i+2, endIndexInclusive=i+2)
        else:
          assert False, "reality error."
        if nextConditionalJump != None:
          if currentInstruction.args[3] == "PLACEHOLDER FOR OPTIONAL SUCCESS JUMP HERE+1":
            currentInstruction.args[3] = nextConditionalJump.args[0]
          elif currentInstruction.args[3] == "PLACEHOLDER FOR OPTIONAL FAILURE JUMP HERE+2":
            currentInstruction.args[3] = nextConditionalJump.args[1]
          else:
            assert False, "reality error."
        else:
          print("couldn't find a conditional jump, but that might be fine.")
          currentInstruction.args[3] = UnresolvedJump(currentInstruction,1) #set non-branching jump.
      else:
        #raise ReplicaSyntaxError("replace instruction at index {} is invalid:\n{}\n".format(i,currentInstruction))
        pass
    elif currentInstruction.name in ["label","conditionalJump","unconditionalJump"]:
      pass
    else:
      replicaSyntaxAssert(currentInstruction.name in ["conditionalJump","unconditionalJump"],"unknown instruction at index {}:\n{}\n".format(i,currentInstruction))
    i += 1
  i = 0
  while i < len(instructions):
    currentInstruction = instructions[i]
    if currentInstruction.name == "conditionalJump":
      del instructions[i]
    else:
      i += 1
  return
  
def processUnconditionalJumps(instructions):
  for i,currentInstruction in enumerate(instructions):
    if currentInstruction.name == "unconditionalJump":
      assert len(currentInstruction.args) == 1
      currentInstruction.name = "replace"
      currentInstruction.args = ["","",currentInstruction.args[0],currentInstruction.args[0]]
      
    
def resolveLabels(instructions):
  labelValues = dict()
  i = 0
  while i < len(instructions):
    currentInstruction = instructions[i]
    if currentInstruction.name == "label":
      nextInstruction = getNextInstructionByName(instructions,"label",startIndexInclusive=i+1,endIndexInclusive=len(instructions),invert=True)
      if nextInstruction == None:
        print("warning: a label has nothing below it, and will resolve to None.")
      labelValues[currentInstruction.args[0]] = nextInstruction
      del instructions[i]
    else:
      i += 1
  for i,currentInstruction in enumerate(instructions):
    for argi,currentArg in enumerate(currentInstruction.args[2:],2):
      if isinstance(currentArg, UnresolvedJump):
        if isinstance(currentArg.reference, UnresolvedLabel):
          assert type(currentArg.reference.name) == str
          if currentArg.reference.name in labelValues:
            currentArg.reference = labelValues[currentArg.reference.name]
          else:
            raise ReplicaLabelError("unknown label: {}.".format(currentArg.reference.name))
            
            
def resolveJumps(instructions):
  for i,currentInstruction in enumerate(instructions):
    for argi,currentArg in enumerate(currentInstruction.args[2:],2):
      if isinstance(currentArg, UnresolvedJump):
        referenceIndex = None
        try:
          referenceIndex = indexUsingIs(instructions, currentArg.reference)
        except IndexError as ie:
          if currentArg.reference == currentArg:
            print("resolveJumps: the unresolved jump references itself, so the reference will be reset to the instruction it is an argument of.")
            currentArg.setReference(currentInstruction)
            referenceIndex = indexUsingIs(instructions, currentArg.reference)
          else:
            raise ie
        #print("for {} at index {}: for arg {} at index {}: resolving jump to {} which is at index {}, will apply an offset of {}.".format(currentInstruction.shortrepr(), i, shortrepr(currentArg), argi, shortrepr(currentArg.reference), referenceIndex, currentArg.offset))
        finalIndex = referenceIndex + currentArg.offset
        currentInstruction.args[argi] = bin(finalIndex)[2:]
        if currentInstruction.args[2] == bin(i)[2:] and currentInstruction.args[3] == bin(i)[2:]:
          print("resolveJumps: WARNING: instruction {} at index {} jumps to itself no matter what!!!!!!".format(currentInstruction,i))