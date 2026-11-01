" Prints, per line, the syntax group name of every byte column as JSON.
" Usage: vim -Nu NONE -i NONE -es --cmd 'let g:rtp="<repo>/vim" | let g:out="<json>"' -S dump_vim.vim <file>
let &runtimepath = g:rtp . ',' . &runtimepath
filetype plugin on
syntax on
doautocmd BufRead
let s:out = []
for s:l in range(1, line('$'))
  let s:row = []
  for s:c in range(1, col([s:l, '$']) - 1)
    call add(s:row, synIDattr(synID(s:l, s:c, 1), 'name'))
  endfor
  call add(s:out, s:row)
endfor
call writefile([json_encode(s:out)], g:out)
qall!
