#visualize SNPs positions from vcf
args <- commandArgs(trailingOnly = T)
data <- read.table(args[1],stringsAsFactors=F, header=F)
fai <- read.table(args[2],stringsAsFactors=F, header=F)
png_name <- args[3]
chr_name <- fai[, 1]
len_chr <- fai[, 2]

#number of digits in the length of the longest chromosome
digits <- trunc(log10(max(len_chr)))
standard <- 10^(digits)
if(max(len_chr) / standard < 2){
  standard <- standard / 5
}else if(max(len_chr) / standard < 5){
  standard <- standard / 2
}

y_axis_at <- seq(0, standard*10, by = standard)
y_axis_lab <- character(0)
if(standard >= 100000){
  st_lab <- standard/1000000
  sign <- 'M'
}else if(standard >= 100){
  st_lab <- standard/1000
  sign <- 'K'
}else{
  st_lab <- standard
  sign <- 'bp'
}
for(i in 0:10){
  y_axis_lab <- c(y_axis_lab, paste0(st_lab * i, sign))
}

png(png_name, height=1440, width=1440, res=200)
par(mar = c(5, 5, 4, 2)) 
plot(-1, type="n", bty="o", ,xaxt="n", yaxt="n", xlab="", ylab="",
	main=paste0(nrow(data), " markers position"), 
	cex.main=2, xlim=c(0,length(len_chr)+1), ylim=c(max(len_chr),0))
axis(side=1, at=1:length(len_chr), las=2, cex.axis=1.7,
     labels=c(chr_name))
axis(side=2, at=y_axis_at, las=2, cex.axis=1.7,
		labels=y_axis_lab)
for(i in 1:length(len_chr)){	
  segments(i, 0, i, len_chr[i])
  data_select <- data[data[1]==chr_name[i], ]
  pos <- data_select[, 2]
  if(length(pos) > 0){
    for(j in 1:length(pos)){
      segments(i-0.3, pos[j], i+0.3, pos[j])
    }
  }
}
dev.off()

