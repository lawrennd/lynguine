#!/usr/bin/env python

# Text utilities

import os
import sys
import re
import shutil
import time
import string
import glob
import datetime
import subprocess

def get_cvs_version(filename : str, full_path : str) -> str:
    """
    Get the CVS version of a file.

    :param filename: The name of the file to get the version of.
    :type filename: str
    :param full_path: The full path to the file.
    :type full_path: str
    :return: The CVS version of the file.
    :rtype: str
    """
    
    # extract CVS version.
    base_dir = os.path.dirname(full_path)
    cvs_filename = os.path.join(base_dir, 'CVS', 'Entries')    
    cvs_ver=''
    if os.path.exists(cvs_filename):
        file = open(cvs_filename, 'r')
        cvs_lines = file.readlines()
        for line in cvs_lines:
            split_vals = line.split('/')        
            if len(split_vals)>2 and split_vals[1]==filename:
                cvs_ver = split_vals[2]
    return cvs_ver

def get_svn_version(filename : str, full_path : str) -> str:
    """
    Get the SVN version of a file.

    :param filename: The name of the file to get the version of.
    :type filename: str
    :param full_path: The full path to the file.
    :type full_path: str
    :return: The SVN version of the file.
    :rtype: str
    """
    
    # extract SVN version.
    base_dir = os.path.dirname(full_path)
    svn_filename = os.path.join(base_dir, '.svn', 'entries')
    
    file_lines = []
    svn_ver ={}
    in_file = 0
    counter = 11
    if os.path.exists(svn_filename):
        file = open(svn_filename, 'r')
        svn_lines = file.readlines()
        for line in svn_lines:
            if re.findall(re.compile(r'^' + filename), line):
                in_file = 1
            if in_file:
                file_lines.append(line)
                counter = counter - 1
                if counter == 0:
                    break
    if in_file:
        svn_ver['type'] = file_lines[1][0:-1]            
        svn_ver['textLastUpdate'] = file_lines[6][0:-1]            
        svn_ver['checkSum'] = file_lines[7][0:-1]            
        svn_ver['lastChange'] = file_lines[8][0:-1]            
        svn_ver['version'] = file_lines[9][0:-1]            
        svn_ver['userName'] = file_lines[10][0:-1]
    else:
        svn_ver = []
    return svn_ver

import subprocess
import os

def get_git_version(filename: str, full_path: str, git_path: str) -> str:
    """
    Get the latest Git version (commit hash) of a file.

    :param filename: The name of the file to get the version of.
    :type filename: str
    :param full_path: The full path to the file.
    :type full_path: str
    :param git_path: The path to the git repository.
    :type git_path: str
    :return: The latest Git commit hash of the file.
    :rtype: str
    """
    base_dir = os.path.dirname(full_path)
    git_filename = os.path.join(base_dir, filename)

    if os.path.exists(git_filename):
        try:
            # Run the git log command to get the latest commit hash
            output = subprocess.check_output(
                ["git", "--git-dir", os.path.join(git_path, '.git'), '--work-tree', base_dir, "log", "-n", "1", "--pretty=format:%H", "--", filename],
                stderr=subprocess.STDOUT
            )
            return output.decode().strip()
        except subprocess.CalledProcessError:
            # Return an empty string or a suitable message if the command fails
            return ""
    else:
        return ""

def read_txt_file(filename : str, dir_name : str=".", comment_char : str="#") -> str:
    """
    Read in a text file ignoring lines that start with a comment character.

    :param filename: The name of the file to read in.
    :type filename: str
    :param dir_name: The directory to read the file from.
    :type dir_name: str
    :param comment_char: The character to use for comments.
    :type comment_char: str
    :return: The contents of the file.
    :rtype: str
    """

    # Read in the file
    fullname = os.path.join(dir_name, filename)
    if os.path.exists(fullname):
        with open(fullname) as file:
            lines = [line for line in file if not line.startswith(comment_char)]
        return "".join(lines)
    else:
        raise FileNotFoundError(f"File {fullname} not found.")
    
def extract_file_details(filename : str, dir_name : str=".", comment_char : str="#", seperator : str=",") -> list[list[str]]:
    """
    Read csv file ignoring empty lines and those that start with a comment character.

    :param filename: The name of the file to read in.
    :type filename: str
    :param dir_name: The directory to read the file from.
    :type dir_name: str
    :param comment_char: The character to use for comments.
    :type comment_char: str
    :param seperator: The character to use for seperating fields.
    :type seperator: str
    :return: The details of the file.
    :rtype: list of lists
    """

    # Read in the file    
    fullname = os.path.join(dir_name, filename);
    details = []
    if os.path.exists(fullname):
        with open(fullname, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line[0]=='#':
                continue
            elif line[0]=='\n':
                continue
            else:
                details.append(line.split(seperator))
    else:
        raise FileNotFoundError(f"File {fullname} not found.")

    for i in range(len(details)):
        for j in range(len(details[i])):
            details[i][j] = details[i][j].strip()

    return details



