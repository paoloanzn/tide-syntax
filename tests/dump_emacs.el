;;; dump_emacs.el --- Dump what tide-lang-mode sees, as JSON  -*- lexical-binding: t; -*-

;; Usage: emacs -Q --batch -l dump_emacs.el MODE-FILE faces FILE OUT
;;        emacs -Q --batch -l dump_emacs.el MODE-FILE compile FILE OUT
;;
;; faces:   visits FILE and writes, per line, the face of every column
;;          ("" for none): [["font-lock-keyword-face", ...], ...].
;; compile: reads FILE as `tide' output in `compilation-mode', matching with
;;          the tide-lang rule only, and writes every message found:
;;          [[file, line, column, type], ...] (type 2 error, 1 warning, 0 note).

;;; Code:

(require 'json)

(pcase-let ((`(,mode-file ,what ,file ,out) command-line-args-left))
  (setq command-line-args-left nil)
  (load (expand-file-name mode-file) nil t)
  (let ((result
         (pcase what
           ("faces"
            (with-current-buffer (find-file-noselect file)
              (unless (eq major-mode 'tide-lang-mode)
                (error "%s opened in %s, not tide-lang-mode" file major-mode))
              (font-lock-ensure)
              (goto-char (point-min))
              (let (lines)
                (while (not (eobp))
                  (let (row)
                    (while (not (eolp))
                      (let ((face (get-text-property (point) 'face)))
                        (push (if face (format "%s" face) "") row))
                      (forward-char))
                    (push (vconcat (nreverse row)) lines))
                  (forward-line))
                (vconcat (nreverse lines)))))
           ("compile"
            (with-temp-buffer
              (insert-file-contents file)
              (compilation-mode)
              (setq-local compilation-error-regexp-alist '(tide-lang))
              (compilation--ensure-parse (point-max))
              (goto-char (point-min))
              (let (messages match)
                (while (setq match (text-property-search-forward 'compilation-message))
                  (let* ((msg (prop-match-value match))
                         (loc (compilation--message->loc msg)))
                    (push (vector (caar (compilation--loc->file-struct loc))
                                  (compilation--loc->line loc)
                                  (compilation--loc->col loc)
                                  (compilation--message->type msg))
                          messages)))
                (vconcat (nreverse messages)))))
           (_ (error "Unknown dump %S" what)))))
    (with-temp-file out
      (insert (json-encode result)))))

;;; dump_emacs.el ends here
