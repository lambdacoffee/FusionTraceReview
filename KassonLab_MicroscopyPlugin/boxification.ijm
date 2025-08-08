/*

*/

info_filepath = getArgument();
text = File.openAsString(info_filepath);
text_lines = split(text, "\n");
labels_arr = newArray(text_lines.length - 1);
filepaths_arr = newArray(text_lines.length - 1);
for (i = 1; i < text_lines.length; i++) {
	curr_line = text_lines[i];
	line_arr = split(curr_line, ",");
	labels_arr[i - 1] = line_arr[0];
	filepaths_arr[i - 1] = line_arr[line_arr.length - 1];
} analysis_pardir = File.getDirectory(info_filepath);	// trailing file separator
fusion_ouput_directory = analysis_pardir + "FusionOutput";	// Detections for changepoints, FusionOutput for manual assignments
fusion_output_file_list = getFileList(fusion_ouput_directory);
for (i=0; i<labels_arr.length; i++) {
	kept_boxes_filepath = analysis_pardir + "Segmentation" + File.separator + labels_arr[i] + File.separator + "keptBoxes.zip";
	open(kept_boxes_filepath);
	matching_fusion_output_filename = "";
	for (j=0; j<fusion_output_file_list.length; j++) {
		if (indexOf(fusion_output_file_list[j], labels_arr[i]) != -1) {
			matching_fusion_output_filename = fusion_output_file_list[j];
		}
	} fusion_output_filepath = fusion_ouput_directory + File.separator + matching_fusion_output_filename;
	fusion_output_text = File.openAsString(fusion_output_filepath);
	fusion_output_lines = split(fusion_output_text, "\n");
	for (j=1; j<fusion_output_lines.length-1; j++) {
		line = split(fusion_output_lines[j], ",");
		if (line[2] == "1") {
			roiManager("select", parseInt(line[0]) - 1);
			roiManager("Set Color", "cyan");
		} if (line[2] == "0") {
			roiManager("select", parseInt(line[0]) - 1);
			roiManager("Set Color", "yellow");
		}
	} roiManager("Associate", "false");
	selectWindow("ROI Manager");
	roiManager("save", kept_boxes_filepath);
	run("Close");
}
