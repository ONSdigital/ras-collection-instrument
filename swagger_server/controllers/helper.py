def is_valid_file_format(file_name, extensions):
    extensions_tuple = tuple([e for e in extensions.split(",")])
    return file_name.endswith(extensions_tuple)
   

def is_valid_file_name_length(file_name, length):
    return len(file_name) <= int(length)

