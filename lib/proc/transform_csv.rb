# Trim the files and write datapoints in csv

datapoints = Array.new
infile = File.new("Books.txt", "r")
outfile = File.new("Books.csv", "w")
datapoint = ""
while (line = infile.gets)
	if line.index('product/productId') != nil  then
        datapoint = ""
		datapoint = datapoint + "#{line[19..-2]},"
    elsif line.index('review/userId') != nil then
    	datapoint = datapoint + "#{line[15..-2]},"
    elsif line.index('review/score') != nil then
    	datapoint = datapoint + "#{line[14..-2]},"
    elsif line.index('review/time') != nil then
    	datapoint = datapoint + "#{line[13..-2]}\n"
        outfile.write(datapoint)
    end
end
infile.close
outfile.close
