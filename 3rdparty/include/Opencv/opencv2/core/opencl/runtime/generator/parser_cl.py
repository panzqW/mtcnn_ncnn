#!/bin/python
# usage:
#     cat opencl11/cl.h | $0 cl_runtime_opencl11
#     cat opencl12/cl.h | $0 cl_runtime_opencl12
import sys, re;

from common import remove_comments, getTokens, getParameters, postProcessParameters

try:
    if len(sys.argv) > 1:
        outfile = open('../../../../include/opencv2/core/opencl/runtime/autogenerated/' + sys.argv[1] + '.hpp', 'wb')
        outfile_impl = open('../autogenerated/' + sys.argv[1] + '_impl.hpp', 'wb')
        outfile_wrappers = open('../../../../include/opencv2/core/opencl/runtime/autogenerated/' + sys.argv[1] + '_wrappers.hpp', 'wb')
        if len(sys.argv) > 2:
            f = open(sys.argv[2], "r")
        else:
            f = sys.stdin
    else:
        sys.exit("ERROR. Specify output file")
except:
    sys.exit("ERROR. Can't open input/output file, check parameters")

fns = []

while True:
    line = f.readline()
    if len(line) == 0:
        break
    assert isinstance(line, str)
    parts = line.split();
    if line.startswith('extern') and line.find('CL_API_CALL') != -1:
        # read block of lines
        while True:
            nl = f.readline()
            nl = nl.strip()
            nl = re.sub(r'\n', r'', nl)
            if len(nl) == 0:
                break;
            line += ' ' + nl

        line = remove_comments(line)

        parts = getTokens(line)

        fn = {}
        modifiers = []
        ret = []
        calling = []
        i = 1
        while (i < len(parts)):
            if parts[i].startswith('CL_'):
                modifiers.append(parts[i])
            else:
                break
            i += 1
        while (i < len(parts)):
            if not parts[i].startswith('CL_'):
                ret.append(parts[i])
            else:
                break
            i += 1
        while (i < len(parts)):
            calling.append(parts[i])
            i += 1
            if parts[i - 1] == 'CL_API_CALL':
                break

        fn['modifiers'] = []  # modifiers
        fn['ret'] = ret
        fn['calling'] = calling

        # print 'modifiers='+' '.join(modifiers)
        # print 'ret='+' '.join(type)
        # print 'calling='+' '.join(calling)

        name = parts[i]; i += 1;
        fn['name'] = name
        print 'name=' + name

        params = getParameters(i, parts)

        fn['params'] = params
        # print 'params="'+','.join(params)+'"'

        fns.append(fn)

f.close()

print 'Found %d functions' % len(fns)

postProcessParameters(fns)

from pprint import pprint
pprint(fns)

from common import *

filterFileName='./filter/opencl_core_functions.list'
numEnabled = readFunctionFilter(fns, filterFileName)

functionsFilter = generateFilterNames(fns)
filter_file = open(filterFileName, 'wb')
filter_file.write(functionsFilter)

ctx = {}
ctx['CL_REMAP_ORIGIN'] = generateRemapOrigin(fns)
ctx['CL_REMAP_DYNAMIC'] = generateRemapDynamic(fns)
ctx['CL_FN_DECLARATIONS'] = generateFnDeclaration(fns)

sys.stdout = outfile
ProcessTemplate('template/opencl_core.hpp.in', ctx)

ctx['CL_FN_INLINE_WRAPPERS'] = generateInlineWrappers(fns)

sys.stdout = outfile_wrappers
ProcessTemplate('template/opencl_core_wrappers.hpp.in', ctx)

ctx['CL_FN_ENTRY_DEFINITIONS'] = generateStructDefinitions(fns)
ctx['CL_FN_ENTRY_LIST'] = generateListOfDefinitions(fns)
ctx['CL_FN_ENUMS'] = generateEnums(fns)
ctx['CL_FN_SWITCH'] = generateTemplates(15, 'opencl_fn', 'opencl_check_fn', 'CL_API_CALL')
ctx['CL_NUMBER_OF_ENABLED_FUNCTIONS'] = '// number of enabled functions: %d' % (numEnabled)

sys.stdout = outfile_impl
ProcessTemplate('template/opencl_core_impl.hpp.in', ctx)
