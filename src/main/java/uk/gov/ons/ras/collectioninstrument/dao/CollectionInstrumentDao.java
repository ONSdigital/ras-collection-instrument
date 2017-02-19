package uk.gov.ons.ras.collectioninstrument.dao;

import org.springframework.data.repository.CrudRepository;
import org.springframework.transaction.annotation.Transactional;

import uk.gov.ons.ras.collectioninstrument.entities.CollectionInstrument;

	@Transactional
	public interface CollectionInstrumentDao extends CrudRepository<CollectionInstrument, Long> {

	  public CollectionInstrument findById(Long id);

	}