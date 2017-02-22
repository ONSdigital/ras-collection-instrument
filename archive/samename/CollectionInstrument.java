//package uk.gov.ons.ras.collectioninstrument.jdbc;
//
//import com.google.gson.Gson;
//import org.springframework.beans.factory.annotation.Autowired;
//import org.springframework.jdbc.core.JdbcTemplate;
//import org.springframework.jdbc.core.PreparedStatementCreator;
//import org.springframework.jdbc.core.RowMapper;
//import org.springframework.jdbc.support.GeneratedKeyHolder;
//import org.springframework.jdbc.support.KeyHolder;
//import org.springframework.stereotype.Repository;
//import org.springframework.transaction.annotation.Transactional;
//
//import javax.persistence.Transient;
//import java.sql.*;
//import java.util.List;
//import java.util.Map;
//
///**
// * Class for accessing the Collection Instrument table.
// * <p>
// * We're using JDBC so that we can get access to the Json column type in Postgres,
// * which seems to be tricky and more complex to do through Hibernate.
// */
//@Repository
//public class CollectionInstrument {
//
//    /**
//     * Represents the Json stored in the content column.
//     * As a convenience, this includes the database ID field when loaded.
//     */
//    public static class Json {
//        @Transient
//        public int id;
//        public String urn;
//        public String ciType;
//        public String surveyId;
//        public Map<String, String> classifiers;
//    }
//
//    /**
//     * NB JdbcTemplate is thread-safe: http://stackoverflow.com/questions/467324/spring-jdbctemplate-and-threading
//     */
//    @Autowired
//    private JdbcTemplate jdbcTemplate;
//
//    static final String selectAll = "select * from ras_collection_instruments";
//    static final String select = "select * from ras_collection_instruments where id=?";
//    static final String insert = "insert into ras_collection_instruments (content) values (?)";
//
//    static class CollectionInstrumentMapper implements RowMapper<Json> {
//        public Json mapRow(ResultSet rs, int rowNum) throws SQLException {
//            Json content = new Gson().fromJson(rs.getString("content"), Json.class);
//            content.id = rs.getInt("id");
//            return content;
//        }
//    }
//
//    @Transactional(readOnly = true)
//    public List<Json> list() {
//        return jdbcTemplate.query(selectAll,
//                new CollectionInstrumentMapper());
//    }
//
//    /**
//     * Reads collection instrument details for the given database row ID.
//     *
//     * @param id The database row ID.
//     * @return A {@link Json} instance representing the database row.
//     */
//    @Transactional(readOnly = true)
//    public Json read(int id) {
//        return jdbcTemplate.queryForObject(
//                select,
//                new Object[]{id}, new CollectionInstrumentMapper());
//    }
//
//    /**
//     * Creates a new Collection Instrument record.
//     *
//     * @param json The {@link Json} instance to be stored.
//     */
//    public Json create(Json json) {
//        KeyHolder holder = new GeneratedKeyHolder();
//        jdbcTemplate.update(new PreparedStatementCreator() {
//            @Override
//            public PreparedStatement createPreparedStatement(Connection connection) throws SQLException {
//                PreparedStatement ps = connection.prepareStatement(insert, Statement.RETURN_GENERATED_KEYS);
//                ps.setString(1, new Gson().toJson(json));
//                return ps;
//            }
//        }, holder);
//
//        json.id = holder.getKey().intValue();
//        return json;
//    }
//}
//
//
//
