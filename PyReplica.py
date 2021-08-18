from PyReplicaCompile import formatCompiledLine

RVM_CONSTANTS = {"INSTRUCTION_DELIMITER":";","ARGUMENT_DELIMITER":"`"}


def coreReplace(data,searchTerm,replacementTerm):
  return (searchTerm in data, data.replace(searchTerm,replacementTerm))
  
class ReplicaVirtualMachine:

  def __init__(self, programTape, dataTape):
    self.programTape, self.dataTape, self.location = programTape, dataTape, 0
    self.splitProgramTape = self.programTape.split(RVM_CONSTANTS["INSTRUCTION_DELIMITER"])
    
  def doCycle(self,quietly=True):
    currentWord = self.splitProgramTape[self.location]
    searchTerm, replacementTerm, successJumpText, failureJumpText = currentWord.split(RVM_CONSTANTS["ARGUMENT_DELIMITER"])
    successful, self.dataTape = coreReplace(self.dataTape, searchTerm, replacementTerm)
    #if not quietly:
    #  print("doCycle: successJumpText={}, failureJumpText={}, successful={}.".format(successJumpText, failureJumpText, successful))
    jumpLocation = int(successJumpText if successful else failureJumpText, 2)
    self.location = jumpLocation
    
  def printState(self):
    print("  /--------------------------------\n  |\n  |{}\n  |\n  |{}\n  |\n  \\-".format(formatCompiledLine(self.location, self.splitProgramTape[self.location]),str(self.dataTape)))
    
  def run(self):
    self.printState()
    lastUserInput = ""
    while True:
      userInput = raw_input("[<steps>[ quietly]|break] >->->")
      if userInput == "":
        userInput = lastUserInput
        if userInput == "":
          continue
      lastUserInput = userInput
      if userInput == "break":
        break
      steps = int((userInput+" ").split(" ")[0])
      quietly = userInput.endswith("quietly")
      for i in range(steps):
        if not quietly:
          self.printState()
        self.doCycle(quietly=quietly)
      self.printState()
    

"""

program to delete everything after x, then delete x:
  rsm = pr.ReplicaVirtualMachine("x0`x`0`1;x1`x`0`10;x``10`10","10101x111000111000")





"""





