#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# Framework written by
# Pascal Bongaertz
# Daniel Goßen
# Hendrik Willing

"""
SYNOPSIS
    co_rr_solver [OPTION] [DIRECTORY]

DESCRIPTION
    All found recurrence relations in DIRECTORY that have filenames matching "comass??.txt"
    are inspected and a direct formula describing these recurrence relations is stored in the
    file "comass??-dir.txt". If DIRECTORY is omitted, the location of "co_rr_solver" is taken
    as directory.

    -v, --verbose
        print debugging information during execution of "co_rr_solver"
"""

import glob  # Library for filename pattern-matching
import sympy as sy
from sympy import sympify, roots, solve, expand, factor
from sympy.abc import r, n
import sys  # For access to the given argument
import os  # Gives access to current location of co_rr_solver

# Global variables:
next_symbolic_var_index = 0  # This variable indicates the next index for the p_x variable names needed for Theorem 6.
print_debug_information = False  # This variable indicates whether debug information should be printed (this is read in using the command line argument list)

"""Print the given list line by line, each line started and ended with a quotation mark."""


def print_list(listing):
    for line in listing:
        print("\"" + line + "\"")


"""Print the dictionary element per element: First key, then ":" and value."""


def print_dict(dictionary):
    for key in dictionary:
        print(str(key) + ": " + str(dictionary[key]))


"""First checks if debug printing is allowed.
   Then checks the type of the input of the function.
   Then prints the input based on the type of input."""


def debug_print(debug_information):
    global print_debug_information
    if print_debug_information:
        if type(debug_information) == dict:
            print_dict(debug_information)
        elif type(debug_information) == list:
            print_list(debug_information)
        else:
            print(str(debug_information))


"""Determines for each line in lines:
    The x-value of s(x) and the corresponding y-value of s(x)=y.
    This is returned as dictionary where x is the integer-key and y the string-value."""


def det_init_conditions(lines):
    conditions = {}
    for line in lines:
        pos_s_bracket = line.find("s(")  # Position of "s("
        start_index_nr = pos_s_bracket + 2  # First index of x-value
        pos_bracket_equal = line.find(")=", pos_s_bracket)  # Position of ")="
        start_index_y = pos_bracket_equal + 2  # First position after the "=" symbol
        x_value = int(line[start_index_nr:pos_bracket_equal])
        y_value = line[start_index_y:]
        conditions[x_value] = y_value
    return conditions


"""Searches for the left begin of the term (beginning at start) and returns the first position belonging to the term, where the symbols are still
    counted as part of the term (may be handy for "+" and "-", but REMIND THIS if the symbols list also contains "*" and "/")..
    The begin of a new term is indicated with one of the symbols in the list "symbols", but only if there are no opened brackets at this position."""


def search_left_term_begin(equation, start, symbols):
    bracket_count = 0  # Indicating the number of opened bracket-scopes
    index = start
    while index >= 0:
        if equation[index] == ")":
            bracket_count += 1
        elif equation[index] == "(":
            bracket_count -= 1
        elif bracket_count == 0 and equation[index] in symbols:
            return index
        index -= 1
    return 0  # If we got until here the term starts at the begin of equation


"""Searches for the right end of the term (beginning at start) and returns the last position belonging to the term.
    The begin of a new term is indicated with one of the symbols in the list "symbols", but only if there are no opened brackets at this position."""

def search_right_term_end(equation, start, symbols):
    bracket_count = 0  # Indicating the number of opened bracket-scopes
    index = start
    while index < len(equation):
        if equation[index] == "(":
            bracket_count += 1
        elif bracket_count == 0 and equation[index] in symbols and index > 0:
            return index - 1
        elif equation[index] == ")":
            bracket_count -= 1
        index += 1
    return len(equation) - 1  # If we got until here the term ends at the end of equation

def reformat_equation(equation):
    equation = equation.replace("**", "^")
    pos_sqrt = equation.find("sqrt(")
    while pos_sqrt >= 0:
        pos_end = search_right_term_end(equation, pos_sqrt + 5, [')'])
        equation = "{0}^(1/2){1}".format(equation[0:pos_end + 2], equation[pos_end + 2:])
        equation = equation.replace("sqrt", "", 1)
        pos_sqrt = equation.find("sqrt(")
    return equation

#def search_right_term_end(equation, start, symbols):
#    bracket_count = 0  # Indicating the number of opened bracket-scopes
#    index = start
#    while index < len(equation):
#        if equation[index] == "(":
#            bracket_count += 1
#        elif equation[index] == ")":
#            bracket_count -= 1
#        elif bracket_count == 0 and equation[index] in symbols and index > 0:
#            return index - 1
#        index += 1
#    return len(equation) - 1  # If we got until here the term ends at the end of equation


"""Determines and returns:
    1. The value of x in s(n-x) as integer, where pos_s should be the index of "s" in equation
    2. equation where "s(n-x)" is replaced by "1"."""


def recurrent_step_length(equation, pos_s):
    exclusive_end_pos = equation.find(")", pos_s)
    value = equation[pos_s + 4:exclusive_end_pos]
    equation = equation.replace("s(n-" + value + ")", "1")  # Replace "s(n-x)" with "1"
    return int(value), equation


"""Determines and returns:
    1. A dictionary of the associated homogeneous recurrence relation in default form, where:
        -The integer-key is x of s(n-x) (thus without minus)
        -The string-value is y of y*s(n-x)
    2. A list of string-terms of F(n)."""


def analyze_recurrence_equation(equation):
    associated = {}
    f_n_list = []
    equation = equation[5:len(equation)]  # Remove the "s(n)="-part
    pos_s = equation.find("s(n-")  # First position of recurrent part
    while pos_s >= 0:  # There is another recurrent s(n-x) part
        debug_print(equation)
        step_length, equation = recurrent_step_length(equation,
                                                      pos_s)  # Determines step length and replaces recurrent part with a "1"
        debug_print(step_length)
        left_pos = search_left_term_begin(equation, pos_s, ["+", "-"])
        right_pos = search_right_term_end(equation, pos_s, ["+", "-"])
        c_n = equation[left_pos:right_pos + 1]  # Substring with both indexes inclusive
        debug_print("c_n " + c_n)
        equation = equation.replace(c_n, "", 1)  # Remove the actual c_n from the equation (only once)
        associated[step_length] = c_n  # Add the recursive step length and factor to the dictionary
        pos_s = equation.find("s(n-")  # First position of recurrent part (because other "s(n-"-part is already removed)
    # Sorry, but you will have to implement the treatment of F(n) yourself!
    if len(equation) > 0:
        equation = str(simplify(equation))
        debug_print("left for F(n): " + equation)
        pos_s = equation.find("**n")
        while pos_s >= 0:
            left_pos = search_left_term_begin(equation, pos_s, ["+", "-"])
            right_pos = search_right_term_end(equation, pos_s, ["+", "-"])
            c_n = equation[left_pos:right_pos + 1]
            equation = equation.replace(c_n, "", 1)
            pos_s = equation.find("**n")
            f_n_list.append(c_n)

        # add a possible remainder of the equation to f(n)
        if len(equation) > 0:
            f_n_list.append(equation)

        debug_print("F(n) list: " + str(f_n_list))
    return associated, f_n_list


"""Reads in all lines of the file except the first, second and last one.
    The lines are returned as list of strings."""


def read_file(filename):
    lines = []
    with open(filename, "r") as input_file:
        for index, line in enumerate(input_file):
            if not (index in [0,
                              1]) and line != "];\n":  # Filter out first and second row and the last that contains "];\n"
                lines.append(line.strip())  # Append and remove leading and closing whitspaces
    return lines


"""Goes through all rows except the last and delete the "," at the end.
    The result is returned (again as list of strings)."""


def clear_commas(lines):
    for index, line in enumerate(lines):
        if index < len(lines) - 1:  # This is not the last line
            comma_pos = len(line) - 1  # The last index position where the "," stands
            lines[index] = line[:comma_pos]
    return lines


"""Deletes all remaining whitespace and converts "^" to "**".
    The result is returned (again as list of strings)."""


def fix_syntax(lines):
    for index, line in enumerate(lines):
        line = str.replace(line, " ", "")
        line = str.replace(line, "^", "**")
        lines[index] = line
    return lines


"""Finds a closed formula for a homogeneous recurrence relation.
    The return value is a string of the right side of the equation "s(n) = ..."""

from sympy import *
from sympy.abc import r
from sympy.parsing.sympy_parser import parse_expr


def solve_polynomial_roots(polynomial):
    solutionsWithMultiplicity = roots(Eq(parse_expr(polynomial), 0), r)
    debug_print("Roots /w multiplicity: " + str(solutionsWithMultiplicity))
    return solutionsWithMultiplicity


def construct_default_from(associated):
    default_form = "s(n) = "
    i = 1
    while i <= len(associated):
        default_form += str(associated[i]) + "s(n - " + str(i) + ")"
        i += 1
    debug_print("Default form: " + default_form)


def build_polynomial(associated):
    degree = max(associated, key=int)
    rvergelijking = "r**" + str(degree)
    for key in associated:
        if degree - key > 1:
            rvergelijking += negate_c_part((associated[key]).split("*")[0]) + "*r**" + str((degree - key))
        elif degree - key == 1:
            rvergelijking += negate_c_part((associated[key]).split("*")[0]) + "*r"
        else:
            rvergelijking += negate_c_part((associated[key]).split("*")[0])



    # rvergelijking = "r**" + str(len(associated))


    # for key in sorted(associated):
    #     associated[key] = (associated[key]).split("*")[0]
    #
    #     # print(str(key) + " : " + str(associated[key]))
    #     cpart = negate_c_part(associated[key])
    #     # print(str(key) + " : " + str(cpart))
    #
    #     rvergelijking += cpart
    #
    #     if (len(associated) - key) > 0:
    #         rvergelijking += "*r**" + str((len(associated) - key))

    debug_print("Characteristic equation: " + rvergelijking)
    return rvergelijking


def negate_c_part(cpart):
    if cpart[0] == "-":
        return "+" + cpart[1:]
    elif cpart[0] == "+":
        return "-" + cpart[1:]
    return "-" + cpart


def build_general_solution(solutionsWithMultiplicity):
    generalSolution = ""
    # for every root place it it's multiplicity times in the general solution
    alphaNumber = 0
    for root in solutionsWithMultiplicity:
        # print("For root: " + str(root))
        for i in range(0, solutionsWithMultiplicity[root]):
            generalSolution += "+ a" + str(alphaNumber) + "*"
            if i is 1:
                generalSolution += "n*"
            elif i > 1:
                generalSolution += "n**" + str(i) + "*"
            generalSolution += "(" + str(root) + ")**n "
            alphaNumber = alphaNumber + 1

    generalSolution = generalSolution[2:]  # remove the first "+ "
    debug_print("Gerneral solution: " + generalSolution)
    return generalSolution


def solve_alphas(generalSolution, init_conditions):
    equations = []
    for n in init_conditions:
        debug_print("   |-find alphas-| " + (generalSolution.replace("n", str(n)) + " = ") + str(init_conditions[n]))
        exrp = parse_expr(generalSolution.replace("n", str(n)))
        eq = Eq(exrp, int(init_conditions[n]))
        equations.append(eq)
    alphaSolutions = solve(equations)
    debug_print("Alpha's: " + str(alphaSolutions))
    return alphaSolutions


def insert_alphas_in_solution(alphas, generalSolution):
    solution = generalSolution
    for alphaSolution in alphas:
        solution = solution.replace(str(alphaSolution), "(" + str(alphas[alphaSolution]) + ")")
    simpleSolution = str(simplify(parse_expr(solution)))
    debug_print("Simple solution found: " + simpleSolution)
    return simpleSolution


def solve_homogeneous_equation(init_conditions, associated):
    # Step 1: Rewrite in the default form
    # construct_default_from(associated)

    # Step 2: Determine characteristic equation
    polynomial = build_polynomial(associated)

    # Step 3: Find roots and multiplicities of characteristic equation
    solutionsWithMultiplicity = solve_polynomial_roots(polynomial)

    # Step 4: Write down general solution
    generalSolution = build_general_solution(solutionsWithMultiplicity)

    # Step 5: Use initial conditions to determine values of the parameters
    alphaSolutions = solve_alphas(generalSolution, init_conditions)
    directFormula = insert_alphas_in_solution(alphaSolutions, generalSolution)

    debug_print("Final solution: S(n)=" + directFormula)
    return directFormula


"""Builds a particular solution for the f(n) part according to theorem 6. Uses the found roots in the homogeneous part 
to decide which form the solution should have"""


def build_particular_solution(f_n_list, solutionsWithMultiplicity):
    # First, we try to rewrite to the form F(n) = (b_tn^t...b_0)s^n
    p_solution = []
    for f in f_n_list:
        pos_s = f.find("n**")
        if pos_s:
            s = search_left_term_begin(f, pos_s, ["+", "-"])  # s should be the the value before this,
            debug_print("S was in pos_s" + str(s))
        else:
            s = 1  # If form is like (n^t + n2^t-1)s^n then s =1

        debug_print("The f(n) part " + str(f) + " got the following s: " + str(s))
        if s in solutionsWithMultiplicity:
            # If s in the solutions, then there exists a solution of the form n^m(b_tn^t...b_0)s^n
            m = solutionsWithMultiplicity[s]
            debug_print("Particular solution m = " + str(m))
            p_solution.append("n**m")
        else:
            # There exists a solution of the form (b_tn^t...b_0)s^n
            p_solution.append("1**n")

    debug_print("Particular solution s = " + str(s))

    return p_solution


"""Finds a closed formula for a nonhomogeneous equation, where the nonhomogeneous part consists
    of a linear combination of constants, "r*n^x" with r a real number and x a positive natural number,
    and "r*s^n" with r and s being real numbers.
    The return value is a string of the right side of the equation "s(n) = ..."""


def solve_nonhomogeneous_equation(init_conditions, associated, f_n_list):
    # # You have to implement this yourself!
    # # Step 1: Rewrite in the default form
    #
    # # Step 2: Determine characteristic equation
    # polynomial = build_polynomial(associated)
    #
    # # Step 3: Find roots and multiplicities of characteristic equation
    # solutionsWithMultiplicity = solve_polynomial_roots(polynomial)
    #
    # # Step 4: Find general solution ofthe associated homogeneous system
    # generalSolution = build_general_solution(solutionsWithMultiplicity)
    #
    # # Step 5: Find a particular solution for step 4
    # particularSolution = build_particular_solution(f_n_list, solutionsWithMultiplicity)
    #
    # # Step 6: Add general solution to particular solution
    # # result = str(generalSolution + particularSolution)
    # result = generalSolution
    # for f_n_sol in f_n_list:
    #     result = str(sympify(result + "+" + f_n_sol))
    #
    # # Step 7: Use initial conditions to determine the exact value of parameters
    # alphaSolutions = solve_alphas(result, init_conditions)
    # directFormula = insert_alphas_in_solution(alphaSolutions, result)
    # return directFormula
    return "Not implemented"

"""Transforms the string equation, that is of the right side of the form "s(n) = ...",
    and wirtes it towards the file "filename", which also needs to contain the desired path."""


def write_output_to_file(filename, equation):
    nr_written_chars = 0
    with open(filename, "w") as output_file:
        nr_written_chars = output_file.write("sdir := n -> {0};\n".format(equation))
    debug_print("Wrote {0} characters to file {1}.".format(str(nr_written_chars), filename))


"""Reformats the for Python needed syntax of equations back to specified output format:
    - "**" is transformed back to "^";
    - "sqrt(...)" is transformed back to "(...)^(1/2)".
    The return value is a string of the modified equation."""


#def reformat_equation(equation):
#    equation = equation.replace("**", "^")
#    pos_sqrt = equation.find("sqrt(")
#    while pos_sqrt >= 0:
#        pos_end = search_right_term_end(equation, pos_sqrt, ["+", "-", "*", "/"])
#        equation = "{0}^(1/2){1}".format(equation[0:pos_end + 1], equation[pos_end + 1:])
#        equation = equation.replace("sqrt", "", 1)
#        pos_sqrt = equation.find("sqrt(")
#    return equation


# Begin of program:
if len(sys.argv) > 3:
    print("Error: Illegal number of arguments.")
else:
    path = str(os.path.dirname(os.path.abspath(__file__)))
    print_debug_information = True
    print(sys.argv)
    if len(sys.argv) > 1:
        argv_index = 1
        if "-v" in sys.argv:
            print_debug_information = True
            if len(sys.argv) > 2:
                argv_index = 2
        elif "--verbose" in sys.argv:
            print_debug_information = True
            if len(sys.argv) > 2:
                argv_index = 2
        if sys.argv[argv_index].find("/") != -1:
            path = sys.argv[argv_index]
    print(path)
    for filename in glob.glob(path + "comass[0-9][0-9].txt"):
        print("File: " + filename)
        next_symbolic_var_index = 0  # Reset this index for every file
        debug_print("Beginning for file \"{0}\"".format(filename))
        lines = read_file(filename)
        lines = clear_commas(lines)
        lines = fix_syntax(lines)
        print("Len lines: " + str(len(lines)))
        debug_print(lines)
        # The following quick fix was done because some input files had two newlines at their end and the list "lines" thus may contain one empty line "" at the end
        tmp = len(lines)
        if lines[len(lines) - 1] == "":
            tmp -= 1
        init_conditions = det_init_conditions([lines[index] for index in range(1, tmp)])  # Determine initial conditions with all but the first line as input
        associated, f_n_list = analyze_recurrence_equation(lines[0])

        # Print debugging information:
        debug_print(filename)
        debug_print("Initial conditions:")
        debug_print(init_conditions)
        debug_print("Associated homogeneous recurrence relation:")
        debug_print(associated)
        debug_print("F(n):")
        debug_print(f_n_list)

        output_filename = filename.replace(".txt", "-dir.txt")
        resulting_equ = ""
        # Check if the equation is a homogeneous relation
        if not f_n_list:  # The list is empty
            resulting_equ = solve_homogeneous_equation(init_conditions, associated)
        else:
            resulting_equ = solve_nonhomogeneous_equation(init_conditions, associated, f_n_list)
        resulting_equ = reformat_equation(resulting_equ)
        write_output_to_file(output_filename, resulting_equ)

        debug_print("#################################\n")
    print("Program is completely executed. There are no more recurrence relations to compute.")
