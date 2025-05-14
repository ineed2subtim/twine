arr=$(ls *.json)
output_file="upstream_ports.txt"
for file in ${arr[@]};
do
       	echo "" >> $output_file;
       	echo "" >> $output_file;
       	echo $file >> $output_file;
       	cat $file | grep Labels | grep '\.....' | uniq  >> $output_file ;
done
