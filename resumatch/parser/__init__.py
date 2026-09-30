# expose parser subpackage

from resumatch.parser.resume_parser import DocumentParser


# test function
def initialize_parser():
    print("Initializing parser....")


# initialize_parser()


__all__ = ["DocumentParser"]
