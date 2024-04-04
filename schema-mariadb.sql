CREATE TABLE `vcf_genotypes` (
  `genome` varchar(10) NOT NULL,
  `contig` varchar(25) NOT NULL,
  `pos` int(10) NOT NULL,
  `ref` varchar(1000) NOT NULL,
  `alt` varchar(1000) NOT NULL,
  `sample` varchar(255) NOT NULL,
  `zigosity` varchar(3),
  `genotype_details` varchar(5000),
  PRIMARY KEY (`genome`,`contig`,`pos`,`ref`(100),`alt`(100),`sample`),
  KEY `by_genome` (`genome`),
  KEY `by_contig` (`contig`),
  KEY `by_pos` (`pos`),
  KEY `by_ref` (`ref`),
  KEY `by_alt` (`alt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;