
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

for (i=0; i<labels_arr.length; i++) {
	dst_subdir = analysis_pardir + "Segmentation" + File.separator + labels_arr[i];
	run("TIFF Virtual Stack...", "open=" + filepaths_arr[i]);
	//open(filepaths_arr[i]);
	//run("Bio-Formats Importer", "open=["+ filepaths_arr[i] +"] autoscale color_mode=Default stack_order=Default");
	//run("Enhance Contrast", "saturated=0.35");
	vid_id = getImageID();
	Image.removeScale();
	run("Subtract Background...", "rolling=3");
	run("Z Project...", "projection=[Sum Slices]");
	// run("Z Project...", "stop=4 projection=[Max Intensity]");	// for photobleaching
	median_id = getImageID();
	setOption("ScaleConversions", true);
	run("16-bit");
	//run("Enhance Contrast...", "saturated=0.35 normalize");
	
	// run("Subtract Background...", "rolling=5");	// for photobleaching
	
	run("Find Maxima...", "prominence=1000 output=[Single Points]");
	// run("Find Maxima...", "prominence=50 output=[Single Points]");	// for photobleaching
	peaks_bin_id = getImageID();
	run("Analyze Particles...", "pixel add");
	roiManager("Show All without labels");
	run("Set Measurements...", "min bounding redirect=None decimal=3");
	selectImage(peaks_bin_id);
	close();
	selectImage(median_id);
	roiManager("Measure");
	selectWindow("Results");
	peaks_filepath = dst_subdir + File.separator + "peaks.csv";
	saveAs("results", peaks_filepath);
	selectWindow("ROI Manager");
	run("Close");
	
	good_particle_idx = newArray();
	bad_particle_idx = newArray();
	for (r=0; r<nResults; r++) {
		peak_val = getResult("Max", r);
		corner_x = getResult("BX", r);
		corner_y = getResult("BY", r);
		run("ROI Manager...");
		
		j = 0;
		width = 1;
		profile_arr = newArray();
		while (width + corner_x - j <= 1024 && width + corner_y - j <= 1024) {
			if (corner_x - j < 0 || corner_y - j < 0) {
				break;
			}
			width = 2 * j + 1;
			makeRectangle(corner_x - j, corner_y - j, width, width);
			if (j != 0) {
				profile_arr = getProfile();
				Array.getStatistics(profile_arr, min, max, mean, stdDev);
				// if (profile_arr[0] < peak_val / 2 || profile_arr[profile_arr.length-1] < peak_val / 2 || profile_arr[0] >= peak_val || profile_arr[profile_arr.length-1] >= peak_val) {
				// if (profile_arr[0] < peak_val * 0.01 || profile_arr[profile_arr.length-1] < peak_val * 0.01 || profile_arr[0] >= peak_val || profile_arr[profile_arr.length-1] >= peak_val) {
				if (profile_arr[0] < max * 0.1 || profile_arr[profile_arr.length-1] < max * 0.1 || profile_arr[0] >= profile_arr[1] || profile_arr[profile_arr.length-1] >= profile_arr[profile_arr.length-2]) {
					break;
				} if (j > 12) {break;}
			} j ++;
		} if (1 < j && j < 12) {
			for (k=0; k<profile_arr.length; k++) {
				if (isNaN(profile_arr[k])) {bad_particle_idx = Array.concat(bad_particle_idx, r);}
			} good_particle_idx = Array.concat(good_particle_idx, r);
		} else {bad_particle_idx = Array.concat(bad_particle_idx, r);}
		roiManager("Add");
		roiManager("Select", r);
		roiManager("Rename", d2s(r + 1, 0));
	}
	roiManager("Select", good_particle_idx);
	Roi.setGroup(1);
	if (bad_particle_idx.length >= 1) {
	roiManager("Select", bad_particle_idx);
	roiManager("Set Color", "red");
	Roi.setGroup(2);
	}
	
	roiManager("show all without labels");
	roi_filepath = dst_subdir + File.separator + "boxes.zip";
	roiManager("Save", roi_filepath);
	selectWindow("Results");
	run("Close");
	
	selectImage(vid_id);
	close("\\Others");
	run("Set Measurements...", "area bounding redirect=None decimal=3");
	selectWindow("ROI Manager");
	run("Select All");
	roiManager("Measure");
	saveAs("Results", dst_subdir + File.separator + "particles.csv");
	run("Close");
	
	selectWindow("ROI Manager");
	if (bad_particle_idx.length >= 1) {
	roiManager("select", bad_particle_idx);
	roiManager("delete");
	} for (j=0; j<roiManager("count"); j++) {
		roiManager("select", j);
		roiManager("rename", d2s(j+1,0));
	} kept_roi_filepath = dst_subdir + File.separator + "keptBoxes.zip";
	roiManager("Save", kept_roi_filepath);
	
	for (n=1; n<nSlices+1; n++) {
		setSlice(n);
		for (p=0; p<roiManager("count"); p++) {
			roiManager("Select", p);
			profile_vals_arr = getProfile();
			Array.getStatistics(profile_vals_arr, min, max, mean, stdDev);
			sum_vals = mean * profile_vals_arr.length;
			setResult(d2s(p+1,0), n-1, sum_vals);
		} 
	} 
	
	// for some reason, this is the only way this works, otherwise 1st intensity vals for all particles are way off???
	setSlice(1);
	for (p=0; p<roiManager("count"); p++) {
		roiManager("Select", p);
		profile_vals_arr = getProfile();
		Array.getStatistics(profile_vals_arr, min, max, mean, stdDev);
		sum_vals = mean * profile_vals_arr.length;
		setResult(d2s(p+1,0), 0, sum_vals);
	} // do not delet the preceding block!
	
	updateResults();
	for (j=0; j<roiManager("count"); j++) {
		time_series_arr = newArray(nResults);
		for (r=0; r<nResults; r++) {
			time_series_arr[r] = getResult(d2s(j+1,0), r);
		} raw_trace = String.join(time_series_arr, ",");
		print("@" + d2s(j+1, 0));
		print(raw_trace);
	}
	selectWindow("Log");
	saveAs("text", analysis_pardir + "ExtractedTraces" + File.separator + labels_arr[i] + "_IntensityTraces.txt");
	close("*");
	selectWindow("Results");
	run("Close");
	selectWindow("Log");
	run("Close");
	selectWindow("ROI Manager");
	run("Close");
}
