<?PHP

	$dir = opendir(getcwd() . "/scrapedata/");
	
	while($subdir = readdir($dir)){
	
		if($dir!="."&&$dir!=".."){
		
			$inner_dir = opendir(getcwd() . "/scrapedata/");
			
			while($subdir = readdir($dir)){
	
				if($subdir!="."&&$subdir!=".."){
			
					if(file_exists(getcwd() . "/scrapedata/" . $subdir . "/index.php")){
					
						$hostdir = opendir(getcwd() . "/hostdata/");
						
						while($host = readdir($hostdir)){
						
							if($host!="."&&$host!=".."){
							
								$innerhostdir = opendir(getcwd() . "/hostdata/" . $host);
								
								while($innerhost = readdir($innerhostdir)){
								
									if($host!="."&&$host!=".."&&strpos($innerhost, $subdir)!==FALSE){
									
										require_once(getcwd() . "/scrapedata/" . $subdir . "/index.php");
									
										$name = explode(".", $subdir);
									
										$func = "get_" . $name[1] . "_page";
										
										$func(urldecode($innerhost), $host);
									
									}
								
								}
							
							}
						
						}
					
					}
	
				}
				
			}			
		
		}
	
	}
	
	
