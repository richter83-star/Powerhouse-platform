#!/usr/bin/env python3  
import sys  
import os  
sys.path.append(os.path.dirname(__file__))  
from sandbox_runner import run_red_team_tests  
if __name__ == "__main__":  
    run_red_team_tests() 
