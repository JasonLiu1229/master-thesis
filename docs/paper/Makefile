.PHONY: clean all

main = NameStudentYear_Thesis
sources = NameStudentYear_Thesis.tex sections/*.tex
includes = 

NameStudentYear_Thesis.pdf : $(sources) $(includes) 
	pdflatex NameStudentYear_Thesis.tex

all:
	pdflatex $(main)
	bibtex $(main)
	pdflatex $(main)
	pdflatex $(main)

clean: 
	rm -f *.toc
	rm -f *.pdf
	rm -f *.out
	rm -f *.lot
	rm -f *.log
	rm -f *.lof
	rm -f *.brf
	rm -f *.blg
	rm -f *.aux
