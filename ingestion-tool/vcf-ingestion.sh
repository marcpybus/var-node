#!/usr/bin/bash

GENOME=$1

if [ "$GENOME" == "grch37" ]; then
    FASTA="/data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz"
elif [ "$GENOME" == "grch38" ]; then
    FASTA="/data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz"
else
    echo "You must define a genome version as argument: grch37 or grch38"
    exit 1
fi

TEMP_DIR=$(mktemp -d /tmp/vcf.XXXX)

echo ""
echo "Processing vcf file..."
cat > $TEMP_DIR/input.vcf
if bgzip -t $TEMP_DIR/input.vcf; then
    mv $TEMP_DIR/input.vcf $TEMP_DIR/input.vcf.gz 
else
    echo "Compressing vcf file..."
    bgzip $TEMP_DIR/input.vcf
fi
echo "Indexing vcf file..."
tabix $TEMP_DIR/input.vcf.gz

echo ""
echo "Filtering only assembled chromosomes..."
echo "     bcftools view -r chr1,1,chr2,2,chr3,3,chr4,4,chr5,5,chr6,6,chr7,7,chr8,8,chr9,9,chr10,10,chr11,11,chr12,12,chr13,13,chr14,14,chr15,15,chr16,16,chr17,17,chr18,18,chr19,19,chr20,20,chr21,21,chr22,22,chrX,X,chrY,Y,chrM,MT"
bcftools view $TEMP_DIR/input.vcf.gz \
    --regions chr1,1,chr2,2,chr3,3,chr4,4,chr5,5,chr6,6,chr7,7,chr8,8,chr9,9,chr10,10,chr11,11,chr12,12,chr13,13,chr14,14,chr15,15,chr16,16,chr17,17,chr18,18,chr19,19,chr20,20,chr21,21,chr22,22,chrX,X,chrY,Y,chrM,MT \
    -o $TEMP_DIR/input.assembled_chromsomes.vcf

echo ""
echo "Converting UCSC chromosomes to GRCh37/38 chromosomes..."
echo "     bcftools annotate --rename-chrs (chr1->1,chr2->2,chr3->3,chr4->4,chr5->5,chr6->6,chr7->7,chr8->8,chr9->9,chr10->10,chr11->11,chr12->12,chr13->13,chr14->14,chr15->15,chr16->16,chr17->17,chr18->18,chr19->19,chr20->20,chr21->21,chr22->22,chrX->X,chrY->Y,chrM->M)"
bcftools annotate --rename-chrs /apps/chromosome_conversion.txt -o $TEMP_DIR/input.grch_chromsomes.vcf $TEMP_DIR/input.assembled_chromsomes.vcf

echo ""
echo "Reference checking, de-multialleling and left-aligning variants..."
echo "     bcftools norm --fasta-ref --multiallelics -any --check-ref wx"
bcftools norm --fasta-ref $FASTA --multiallelics -any --check-ref wx -o $TEMP_DIR/input.normalized.vcf $TEMP_DIR/input.grch_chromsomes.vcf

echo ""
echo "Uploading filtered genotypes to database..."
python3 /apps/vcf-data-upload.py $GENOME $TEMP_DIR/input.normalized.vcf

echo ""
rm -r $TEMP_DIR

