
function determineIfFiji() {
	/*
 	* This function determines if Fiji is being used.
 	* returns: boolean 
 	* 	- true if Fiji.app, else false (ImageJ)
 	*/
	startup_path = getDirectory("startup");
	startup_path_split = split(startup_path, File.separator);
	if (indexOf(startup_path_split[startup_path_split.length-1], "Fiji") != -1)
		{return true;}
	else {return false;}
}

function createWelcome(help_filepath) {
	help_txt = File.openAsString(help_filepath);
	title = "Welcome!";
	if (determineIfFiji()) {Dialog.createNonBlocking(title);}
	else {Dialog.create(title);}
	message = "This is the Kasson Tool extension plugin for Fiji (Fiji Is Just ImageJ).";
	message += "\nThis plugin utilizes Fiji & Python for performing semi-automated analysis workflows related to viral fusion.";
	message += "\nPlease ensure that Python is installed.";
	message += "\nClick 'OK' to continue, 'Cancel' to exit anytime, & 'Help' to display the User Guide.";
	Dialog.addMessage(message);
	Dialog.addHelp(help_txt);
	Dialog.show();
	return 0;
}

function err(error_code) {
	if (error_code == -1) {
		message = "FATAL ERROR: Unsupported File Type!";
	} else if (error_code == -2) {
		message = "FATAL ERROR: Cannot locate summary.txt file!";
	} else if (error_code == -3) {
		message = "FATAL ERROR: Empty directory for source data...!";
	} else if (error_code == -5) {
		message = "FATAL ERROR - ALTERED CORE CONTENTS: Missing interface file!";
	} else if (error_code == -6) {
		message = "FATAL ERROR - ALTERED CORE CONTENTS: Missing interface file!";
	} else if (error_code == -7) {
		message = "FATAL ERROR - Misconfigured summary.txt file - HEADER NOT FOUND";
	} else if (error_code == -8) {
		message = "FATAL ERROR - Broken correlation between media type and representing color...";
	} else if (error_code == -9) {
		message = "FATAL ERROR - FLow pathing conflict - destination folder cannot be a subdirectory of source folder!";
		message += "\nPlease check source directory before attempting processing again.";
	} else if (error_code == -10) {
		message = "FATAL ERROR - DESTINATION 'TEMP' DIRECTORY ALREADY EXISTS!";
		message += "\nPlease rename or move the current destination directory from";
		message += "\nthe Fiji.app directory.";
	} else if (error_code == -11) {
		message = "FATAL CODE ERROR - function arrGet() has been incorrectly fed!";
	} message += "\nTERMINATING SEQUENCE - abort process...";
	exit(message);
}

function arrGet(array, arg) {
	/*Returns first index of arg in array if match is found, returns -1 if not.*/
	for (i=0; i<array.length; i++) {
		if (array[i] == arg) {return i;}
	} return -1;
}

function specifyKassonLibDir() {
	showMessage("KassonLib Location", "Please specify the location of the KassonLib directory!");
	dir_path = getDirectory("Location of KassonLib...");
	return dir_path;
}

function getKassonLibDir() {
	res_dir = getDirectory("macros") + "KassonLib" + File.separator;	
	if (!File.exists(res_dir)) {
		res_dir = getDirectory("macros") + "KassonLib-master" + File.separator;
		if (!File.exists(res_dir)) {
			kasson_lib_info_path = getDirectory("macros") + "KassonLibInfo.txt";
			if (!File.exists(kasson_lib_info_path)) {
				res_dir = specifyKassonLibDir();
				txt_file = File.open(kasson_lib_info_path);
				print(txt_file, res_dir);
				File.close(txt_file);
			} else {
				res_dir = File.openAsString(kasson_lib_info_path);
				res_dir = replace(res_dir, "\n", "");
				if (!File.exists(res_dir)) {
					File.delete(kasson_lib_info_path);
					res_dir = getKassonLibDir();
				}
			}
		}
	} return res_dir;
}

function getSourceFiles(analysis_pardir) {	
	instructions = "Select an option below.\nYou can change the unique data label too.\n";
	instructions += "Only alphanumeric characters and hypen '-' allowed!";
	source_filepaths_arr = newArray();
	source_labels_arr = newArray();
	while (true) {
		filepath = File.openDialog("Select video file to include...");
		filepath = newArray(filepath);
		source_filepaths_arr = Array.concat(source_filepaths_arr, filepath);
		datum_label = newArray("Datum-" + d2s(source_labels_arr.length + 1,0));
		source_labels_arr = Array.concat(source_labels_arr, datum_label);
		title = "Source files and correlating data labels.";
		Dialog.createNonBlocking(title);
		Dialog.setInsets(5, 68, 5);
		Dialog.addMessage(instructions);
		for (i=0; i<source_filepaths_arr.length; i++) {
			Dialog.addString("Label #" + d2s(i+1,0), source_labels_arr[i], 10);
			Dialog.addString("Filepath #" + d2s(i+1,0), source_filepaths_arr[i], 80);
		} radio_items = newArray("Continue with selection", "Add new video file");
		Dialog.addRadioButtonGroup("Options", radio_items, 1, 2, radio_items[0]);
		Dialog.show();
		user_choice = Dialog.getRadioButton();
		for (i = 0; i < source_filepaths_arr.length * 2; i++) {
			str = Dialog.getString();
			if (i % 2 == 0) {
				source_labels_arr[i / 2] = str;
			}
		} if (user_choice == radio_items[1]) {continue;}
		else {break;}
	} dst_filepath = analysis_pardir + "info.txt";
	file = File.open(dst_filepath);
	text = "Label,Filepath\n";
	for (i = 0; i < source_filepaths_arr.length; i++) {
		line = source_labels_arr[i] + "," + source_filepaths_arr[i] + "\n";
		text += line;
	} print(file, text);
	File.close(file);
	return dst_filepath;
}

function setParameters(info_filepath) {
	text = File.openAsString(info_filepath);
	text_lines = split(text, "\n");
	labels_arr = newArray(text_lines.length - 1);
	filepaths_arr = newArray(text_lines.length - 1);
	for (i = 1; i < text_lines.length; i++) {
		curr_line = text_lines[i];
		line_arr = split(curr_line, ",");
		labels_arr[i - 1] = line_arr[0];
		filepaths_arr[i - 1] = line_arr[1];
	} Dialog.createNonBlocking("Set starting frames for analysis.");
	for (i = 0; i < labels_arr.length; i++) {
		Dialog.addNumber(labels_arr[i] + " start frame:", 0);
	} Dialog.show();
	frames_arr = newArray(labels_arr.length);
	for (i = 0; i < frames_arr.length; i++) {
		frames_arr[i] = d2s(Dialog.getNumber(),0);
	} Dialog.createNonBlocking("Set acquisition rate for analysis.");
	for (i = 0; i < labels_arr.length; i++) {
		Dialog.addNumber(labels_arr[i] + " acquisition rate:", 1, 3, 8, "[seconds]");
	} Dialog.show();
	time_intervals_arr = newArray(labels_arr.length);
	for (i = 0; i < time_intervals_arr.length; i++) {
		time_intervals_arr[i] = d2s(Dialog.getNumber(),3);
	} updated_text = "Label,StartFrame,TimeInterval[s],Filepath\n";
	for (i = 0; i < text_lines.length - 1; i++) {
		updated_line_arr = newArray(labels_arr[i], frames_arr[i], time_intervals_arr[i], filepaths_arr[i]);
		updated_line = String.join(updated_line_arr, ",");
		updated_text += updated_line + "\n";
	} file = File.open(info_filepath);
	print(file, updated_text);
	File.close(file);
	return 0;
}

function createSubdirs(analysis_pardir) {
	subdir_arr = newArray("FusionOutput", "ExtractedTraces", "Segmentation");
	for (i=0; i<subdir_arr.length; i++) {
		filepath = analysis_pardir + subdir_arr[i];
		File.makeDirectory(filepath);
	} info_filepath = analysis_pardir + "info.txt";
	text = File.openAsString(info_filepath);
	text_lines = split(text, "\n");
	for (i = 1; i < text_lines.length; i++) {
		curr_line = text_lines[i];
		line_arr = split(curr_line, ",");
		label = line_arr[0];
		subdir_path = analysis_pardir + "Segmentation" + File.separator + label;
		File.makeDirectory(subdir_path);
	}
}

function main() {
	kasson_lib_dir = getKassonLibDir();
	help_filepath = kasson_lib_dir + "log" + File.separator + "help.txt";
	createWelcome(help_filepath);
	
	Dialog.createNonBlocking("Instructions");
	Dialog.addMessage("You will be taken through 3 menus where you can:\n");
	Dialog.setInsets(5, 50, 5);
	instructions = "- add video files to analyze and label them\n";
	instructions += "- add the starting frame for analysis of dwell times\n";
	instructions += "- add the aquistion rate for calculation of dwell times\n";
	Dialog.addMessage(instructions);
	Dialog.show();
	
	analysis_parent_directory = getDirectory("Please select directory for analysis destination...");	// trailing file separator
	
	info_filepath = getSourceFiles(analysis_parent_directory);
	setParameters(info_filepath);
	createSubdirs(analysis_parent_directory);
	
	showMessage("Parameters set & subdirectories created.\nProceding to trace extraction.");
	// vid_seg_script = "C:\\Users\\marcos\\Desktop\\KassonLib-gamma\\scripts\\gamma_ijm\\vid_seg_script.ijm";
	vid_seg_script = kasson_lib_dir + "scripts" + File.separator + "gamma_ijm" + File.separator + "vid_seg_script.ijm";
	runMacro(vid_seg_script, info_filepath);
}

main();
//run("Quit");
