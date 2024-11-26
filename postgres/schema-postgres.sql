

CREATE TABLE vcf_genotypes (
  id BIGSERIAL PRIMARY KEY ,
  genome VARCHAR(6) NOT NULL,
  contig VARCHAR(2) NOT NULL,
  sample VARCHAR(50) NOT NULL,
  pos INTEGER NOT NULL,
  ref VARCHAR(1000) NOT NULL,
  alt VARCHAR(1000) NOT NULL,
  zigosity VARCHAR(3) NOT NULL,
  genotype_data JSON NOT NULL
);

CREATE INDEX vcf_genotypes_by_genome ON vcf_genotypes (genome);
CREATE INDEX vcf_genotypes_by_contig ON vcf_genotypes (contig);
CREATE INDEX vcf_genotypes_by_sample ON vcf_genotypes (sample);
CREATE INDEX vcf_genotypes_by_pos ON vcf_genotypes (pos);
CREATE INDEX vcf_genotypes_by_ref ON vcf_genotypes (ref);
CREATE INDEX vcf_genotypes_by_alt ON vcf_genotypes (alt);

CREATE TABLE vcf_samples (
  genome VARCHAR(6) NOT NULL,
  sample VARCHAR(50) NOT NULL,
  sample_data JSON,
  PRIMARY KEY (genome,sample)
);
CREATE INDEX vcf_samples_by_genome ON vcf_samples (genome);
CREATE INDEX vcf_samples_by_sample ON vcf_samples (sample);

CREATE TABLE available_genomes (
  genome VARCHAR(6) NOT NULL,
  PRIMARY KEY (genome)
);

